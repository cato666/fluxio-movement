import json
from datetime import datetime, timezone
from uuid import UUID

import pytest

from app import main
from app.models import AIObservation, AIReasoningRun, Analysis, CoachReview
from app.seed import DEMO_ATHLETE_ID
from app.services import ai_reasoning


RESULT = {
    'video': {'duration_s': 8},
    'exercise_profile': {'id': 'squat-side', 'version': '1.0', 'view': 'side'},
    'pose_quality': {'average_confidence': .88, 'valid_samples': 120, 'confidence': 'high'},
    'repetition_count_confidence': 'high',
    'summary_metrics': {'min_knee_angle': 95, 'max_trunk_from_vertical': 22},
    'repetitions': [{'repetition': 1, 'start_s': 0, 'bottom_s': 1, 'end_s': 2, 'min_knee_angle': 95, 'pose_confidence': .88, 'count_confidence': 'high'}],
}


def response(observations=None):
    return {'output_text': json.dumps({'observations': [{
        'repetition': 1, 'timestamp': 1.0, 'category': 'trayectoria', 'severity': 'review',
        'title': 'Patrón para revisar', 'description': 'La repetición muestra una variación medible.',
        'evidence': 'min_knee_angle: 95° en Rep 1.', 'confidence': 'medium',
    }] if observations is None else observations, 'summary': 'Revisar la variación entre repeticiones.'}), 'usage': {'input_tokens': 120, 'output_tokens': 80, 'output_tokens_details': {'reasoning_tokens': 30}}}


def login(client, username, password='demo1234'):
    assert client.post('/api/auth/login', json={'username': username, 'password': password}).status_code == 200


def completed_analysis(session, analysis_id='ai-analysis'):
    row = Analysis(id=analysis_id, athlete_id=DEMO_ATHLETE_ID, status='COMPLETED', exercise='Sentadilla', original_filename='x.mp4', video_path='uploads/x.mp4', annotated_video_path='results/x/annotated.mp4', result=RESULT, completed_at=datetime.now(timezone.utc), progress=100)
    session.add(row); session.commit()
    return row


def test_reasoning_enabled_uses_strict_compact_input(monkeypatch):
    monkeypatch.setenv('AI_REASONING_ENABLED', 'true')
    monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
    captured = {}
    def fake_request(payload, _key):
        captured['payload'] = payload
        return response()
    monkeypatch.setattr(ai_reasoning, '_request', fake_request)
    result = ai_reasoning.run_reasoning('Sentadilla', 'side', RESULT)
    assert result.model == 'gpt-5.6-terra'
    assert len(result.observations) == 1
    compact = ai_reasoning.build_input('Sentadilla', 'side', RESULT)
    assert 'timeline' not in compact and compact['repetitions'][0]['number'] == 1
    assert compact['pose_quality']['confidence'] == 'high'
    assert compact['repetitions'][0]['count_confidence'] == 'high'
    assert compact['events'] == [
        {'repetition': 1, 'type': 'start', 'timestamp_s': 0},
        {'repetition': 1, 'type': 'bottom', 'timestamp_s': 1},
        {'repetition': 1, 'type': 'end', 'timestamp_s': 2},
    ]
    assert compact['reasoning_eligibility']['can_generate_observations'] is True
    assert captured['payload']['text']['format']['type'] == 'json_schema'
    assert captured['payload']['text']['format']['strict'] is True
    assert 'evidence' in captured['payload']['text']['format']['schema']['properties']['observations']['items']['required']


def test_reasoning_disabled_does_not_call_openai(monkeypatch):
    monkeypatch.setenv('AI_REASONING_ENABLED', 'false')
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    monkeypatch.setattr(ai_reasoning, '_request', lambda *_: pytest.fail('OpenAI no debe llamarse'))
    assert ai_reasoning.run_reasoning('Sentadilla', 'side', RESULT) is None


def test_reasoning_rejects_more_than_five_observations(monkeypatch):
    monkeypatch.setenv('AI_REASONING_ENABLED', 'true'); monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
    monkeypatch.setattr(ai_reasoning, '_request', lambda *_: response([response()['output_text'] for _ in range(6)]))
    with pytest.raises(ValueError):
        ai_reasoning.run_reasoning('Sentadilla', 'side', RESULT)


def test_reasoning_deduplicates_equivalent_model_observations(monkeypatch):
    monkeypatch.setenv('AI_REASONING_ENABLED', 'true'); monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
    repeated = json.loads(response()['output_text'])['observations'][0]
    monkeypatch.setattr(ai_reasoning, '_request', lambda *_: response([repeated, dict(repeated)]))
    result = ai_reasoning.run_reasoning('Sentadilla', 'side', RESULT)
    assert len(result.observations) == 1


def test_reasoning_abstains_when_pose_or_count_confidence_is_insufficient(monkeypatch):
    monkeypatch.setenv('AI_REASONING_ENABLED', 'true'); monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
    low_quality = {**RESULT, 'pose_quality': {'average_confidence': .42, 'confidence': 'low'}, 'repetition_count_confidence': 'low'}
    monkeypatch.setattr(ai_reasoning, '_request', lambda *_: response())
    result = ai_reasoning.run_reasoning('Sentadilla', 'side', low_quality)
    assert result.observations == []
    assert 'evidencia suficiente' in result.summary


def test_reasoning_accepts_an_explicit_empty_observation_list(monkeypatch):
    monkeypatch.setenv('AI_REASONING_ENABLED', 'true'); monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
    monkeypatch.setattr(ai_reasoning, '_request', lambda *_: response([]))
    result = ai_reasoning.run_reasoning('Sentadilla', 'side', RESULT)
    assert result.observations == []


def test_reasoning_replaces_ungrounded_numeric_evidence_with_source_metrics(monkeypatch):
    monkeypatch.setenv('AI_REASONING_ENABLED', 'true'); monkeypatch.setenv('OPENAI_API_KEY', 'test-key')
    invalid = json.loads(response()['output_text'])['observations'][0]
    invalid['evidence'] = 'min_knee_angle: 999° en Rep 1.'
    monkeypatch.setattr(ai_reasoning, '_request', lambda *_: response([invalid]))
    result = ai_reasoning.run_reasoning('Sentadilla', 'side', RESULT)
    assert result.observations[0]['evidence'] == 'Rep 1 · bottom_s: 1.00 s · min_knee_angle: 95.0°'


def test_reasoning_persists_observations_and_usage(session, monkeypatch):
    completed_analysis(session)
    monkeypatch.setattr(main, 'run_reasoning', lambda *_: ai_reasoning.ReasoningResult([json.loads(response()['output_text'])['observations'][0]], 'Resumen', 'mock-model', {'input_tokens': 12, 'output_tokens': 8}, 4))
    main._run_ai_reasoning('ai-analysis', 'Sentadilla', 'side', RESULT)
    observation = session.scalar(__import__('sqlalchemy').select(AIObservation).where(AIObservation.analysis_id == 'ai-analysis'))
    assert observation.title == 'Patrón para revisar'
    assert observation.evidence == 'min_knee_angle: 95° en Rep 1.'
    assert session.scalar(__import__('sqlalchemy').select(AIReasoningRun).where(AIReasoningRun.analysis_id == 'ai-analysis')).input_tokens == 12
    assert session.get(Analysis, 'ai-analysis').result['ai_reasoning_summary'] == 'Resumen'


def test_openai_error_keeps_analysis_completed_and_marks_run_failed(session, monkeypatch):
    completed_analysis(session)
    monkeypatch.setattr(main, 'run_reasoning', lambda *_: (_ for _ in ()).throw(RuntimeError('provider down')))
    main._run_ai_reasoning('ai-analysis', 'Sentadilla', 'side', RESULT)
    assert session.get(Analysis, 'ai-analysis').status == 'COMPLETED'
    assert session.scalar(__import__('sqlalchemy').select(AIReasoningRun).where(AIReasoningRun.analysis_id == 'ai-analysis')).status == 'FAILED'


def test_athlete_detail_excludes_review_moment_copies(client, session):
    login(client, 'gaston')
    completed_analysis(session, 'deduplicated-detail')
    original = AIObservation(analysis_id='deduplicated-detail', body='IA', title='Patrón', description='Texto', severity='review', confidence='medium', timestamp_s=1.0)
    duplicate = AIObservation(analysis_id='deduplicated-detail', body='Momento', title='Patrón', description='Texto', severity='review', confidence='medium', timestamp_s=1.0, model='deterministic-review-moments')
    session.add_all([original, duplicate]); session.flush()
    from app.models import AIReviewMoment
    session.add(AIReviewMoment(analysis_id='deduplicated-detail', observation_id=duplicate.id, timestamp_s=1.0, reason='ranking', confidence='medium', priority_score=.8))
    session.commit()
    payload = client.get('/api/analyses/deduplicated-detail').json()
    assert [item['id'] for item in payload['ai_observations']] == [str(original.id)]


def test_coach_can_confirm_or_dismiss_only_own_analysis(client, session):
    login(client, 'carlos')
    completed_analysis(session)
    observation = AIObservation(analysis_id='ai-analysis', body='IA', title='IA', description='Detalle', severity='review', confidence='medium')
    review = CoachReview(analysis_id='ai-analysis', athlete_id=DEMO_ATHLETE_ID, coach_id=UUID('00000000-0000-4000-8000-000000000002'), status='IN_REVIEW')
    session.add_all([observation, review]); session.commit()
    url = f'/api/coach/reviews/{review.id}/ai-observations/{observation.id}?coach_id={review.coach_id}'
    assert client.patch(url, json={'decision': 'CONFIRMED'}).json()['decision'] == 'CONFIRMED'
    assert client.patch(url, json={'decision': 'DISMISSED', 'title': 'Editada', 'description': 'Texto editado'}).json()['title'] == 'Editada'
    other = UUID('00000000-0000-4000-8000-000000000003')
    assert client.patch(f'/api/coach/reviews/{review.id}/ai-observations/{observation.id}?coach_id={other}', json={'decision': 'CONFIRMED'}).status_code == 403


def test_internal_usage_aggregates_completed_runs(client, session):
    login(client, 'admin')
    completed_analysis(session, 'usage-completed')
    completed_analysis(session, 'usage-pending')
    session.add_all([
        AIReasoningRun(analysis_id='usage-completed', status='COMPLETED', model='test-model', input_tokens=120, output_tokens=80, reasoning_tokens=30),
        AIReasoningRun(analysis_id='usage-pending', status='FAILED', model='test-model', input_tokens=99, output_tokens=2),
    ])
    session.commit()
    payload = client.get('/api/internal/ai-usage').json()
    assert payload['totals'] == {'completed_runs': 1, 'input_tokens': 120, 'output_tokens': 80, 'reasoning_tokens': 30, 'total_tokens': 200}
    assert payload['by_model'] == [{'model': 'test-model', 'runs': 1, 'input_tokens': 120, 'output_tokens': 80, 'total_tokens': 200}]
    assert {run['status'] for run in payload['recent_runs']} == {'COMPLETED', 'FAILED'}
