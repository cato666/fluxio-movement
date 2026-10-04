import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.services.exercise_library import (
    ExerciseLibrary, ExerciseFinding, ReferenceVideo, ReferenceSegment, LibraryExercise,
)
from app.services.exercise_profiles import ExerciseProfile, ExerciseProfileLoader


IDS = 'air_squat front_squat overhead_squat deadlift clean power_clean snatch power_snatch push_press push_jerk thruster wall_ball box_jump kipping_pull_up chest_to_bar toes_to_bar bar_muscle_up handstand_push_up wall_walk pistol_squat'.split()


@pytest.mark.parametrize('exercise', ['squat', 'deadlift', 'clean'])
def test_old_profiles_unchanged(exercise):
    profile = ExerciseProfileLoader().load(exercise)
    assert profile.transitions and profile.library.reference_videos == []


@pytest.mark.parametrize('exercise_id', IDS)
def test_new_exercises(exercise_id):
    item = ExerciseLibrary().get(exercise_id)
    assert item.priority == 'P1' and item.phases and item.faults and item.metadata
    assert item.required_landmarks and item.supported_views
    assert all(not fault.detectable for fault in item.faults)


def test_optional_metadata_on_detector():
    source = Path('app/services/exercise_profiles/clean_side.json')
    raw = json.loads(source.read_text())
    old = ExerciseProfile.from_dict(raw)
    raw.update(name='Clean', category='weightlifting', phases=['setup', 'catch'])
    new = ExerciseProfile.from_dict(raw)
    assert old.transitions == new.transitions
    assert old.thresholds == new.thresholds
    assert new.library.name == 'Clean'


def test_unknown_exercise():
    with pytest.raises(KeyError):
        ExerciseLibrary().get('unknown')


@pytest.mark.parametrize('field,value', [('category', 'weightlifting'), ('priority', 'P1'), ('analysis_status', 'reference_only')])
def test_filters(field, value):
    items = ExerciseLibrary().list(**{field: value})
    assert items and all(getattr(item, field) == value for item in items)


def video(**changes):
    return dict(provider='youtube', organization='CrossFit', source_type='official',
                video_id='Ty14ogq_Vok', url='https://www.youtube.com/watch?v=Ty14ogq_Vok', **changes)


def test_youtube_reference_and_embed():
    reference = ReferenceVideo.model_validate(video(segments=[dict(type='correct_execution', start_sec=0, end_sec=5)]))
    assert reference.embed_url(0) == 'https://www.youtube.com/embed/Ty14ogq_Vok?start=0&end=5'


@pytest.mark.parametrize('url', ['http://www.youtube.com/watch?v=Ty14ogq_Vok', 'https://evil.example/watch?v=Ty14ogq_Vok', 'https://www.youtube.com/watch?v=aaaaaaaaaaa'])
def test_invalid_reference(url):
    raw = video()
    raw['url'] = url
    with pytest.raises(ValidationError):
        ReferenceVideo.model_validate(raw)


@pytest.mark.parametrize('start,end', [(-1, 5), (5, 5), (6, 5), (0, float('inf')), (float('nan'), 5)])
def test_invalid_timestamps(start, end):
    with pytest.raises(ValidationError):
        ReferenceSegment(type='correct_execution', start_sec=start, end_sec=end)


def test_profile_without_video():
    raw = ExerciseLibrary().get('power_clean').model_dump()
    raw.pop('reference_videos')
    assert LibraryExercise.model_validate(raw).reference_videos == []


def test_future_finding():
    finding = ExerciseFinding(exercise_id='clean', rep=3, fault_id='early_arm_bend', severity='medium', start_sec=13.1, end_sec=15.7, confidence=.87)
    assert finding.confidence == .87
    with pytest.raises(ValidationError):
        ExerciseFinding(**{**finding.model_dump(), 'end_sec': 12})


def test_api_filters_and_unknown(athlete_client):
    assert len(athlete_client.get('/api/exercises').json()) == 20
    for field, value in [('category', 'weightlifting'), ('priority', 'P1'), ('analysis_status', 'reference_only')]:
        response = athlete_client.get('/api/exercises', params={field: value})
        assert response.status_code == 200
        assert response.json() and all(item[field] == value for item in response.json())
    assert athlete_client.get('/api/exercises?category=unknown').json() == []
    assert athlete_client.get('/api/exercises/clean').json()['analysis_status'] == 'supported'
    assert athlete_client.get('/api/exercises/unknown').status_code == 404
    assert athlete_client.get('/exercises').status_code == 200


def test_library_is_authenticated(client):
    assert client.get('/api/exercises').status_code == 401
