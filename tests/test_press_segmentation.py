import copy

from app import main
from app.services.analyzer import _is_press, _segment_press_reps
from tests.test_api import RESULT
from tests.analysis_helpers import write_analysis


def test_press_segments_cycles_from_low_position_to_lockout():
    reps = _segment_press_reps(
        [0, 0.5, 1.0, 1.5, 2.0],
        [120, 135, 168, 132, 166],
        [0.01, 0.03, 0.18, 0.02, 0.16],
    )
    assert reps == [
        {'repetition': 1, 'start_s': 0.5, 'bottom_s': 0.5, 'end_s': 1.0,
         'min_elbow_angle': 135.0, 'lockout_elbow_angle': 168.0},
        {'repetition': 2, 'start_s': 1.5, 'bottom_s': 1.5, 'end_s': 2.0,
         'min_elbow_angle': 132.0, 'lockout_elbow_angle': 166.0},
    ]


def test_press_requires_a_low_position_before_lockout():
    assert _segment_press_reps([0, 0.5], [170, 168], [0.2, 0.19]) == []


def test_press_does_not_reset_the_cycle_when_only_the_elbow_is_still_low():
    reps = _segment_press_reps(
        [0, 0.33, 0.42, 0.67],
        [60, 62, 140, 166],
        [0.03, 0.09, 0.12, 0.13],
    )
    assert reps[0]['start_s'] == 0
    assert reps[0]['end_s'] == 0.67


def test_press_exercise_names_are_recognized_without_changing_other_exercises():
    assert _is_press('Press')
    assert _is_press('press militar')
    assert not _is_press('Sentadilla')


def test_press_analysis_passes_the_exercise_to_the_existing_analyzer(athlete_client, monkeypatch, valid_preflight):
    captured = {}

    def analyzer(_video, _output, exercise=None, *_args, **_kwargs):
        captured['exercise'] = exercise
        return write_analysis(_output, copy.deepcopy(RESULT))

    monkeypatch.setattr(main, 'analyze_video', analyzer)
    response = athlete_client.post(
        '/api/analyses',
        data={'exercise': 'Press', 'objective': 'Bloqueo sobre la cabeza'},
        files={'file': ('press.mp4', b'video', 'video/mp4')},
    )
    assert response.status_code == 202
    assert captured['exercise'] == 'Press'
