from dataclasses import replace
import json
from pathlib import Path

import pytest

from app.services.experimental_faults import DETECTORS, EXPERIMENTS, EvaluationContext

FIXTURE = json.loads(Path('tests/fixtures/experimental_faults.json').read_text())


def build(exercise, case='incorrect'):
    spec = EXPERIMENTS[exercise]
    fixture = FIXTURE['cases'][case]
    context = EvaluationContext(
        exercise_id=fixture.get('exercise_id', exercise), view='side', variant=spec.variant,
        phase=spec.phase, phase_start=1., phase_end=1.4, phase_reviewed=True,
        complete_attempt=fixture.get('complete_attempt', True), calibration_angle=175,
        calibration_reviewed=True, geometry_verified=True,
    )
    samples = [dict(time_s=time, **{spec.metric: angle}, pose_confidence=.95,
                    active_side='both', landmark_visibility={str(i): .95 for i in range(33)},
                    wrist_lift=.12, inverted_body_ratio=.8)
               for time, angle in zip(FIXTURE['times'], fixture['angles'])]
    if fixture.get('remove_visibility'):
        for sample in samples:
            sample.pop('landmark_visibility')
    if fixture.get('duplicate_only'):
        samples = [samples[0].copy() for _ in range(8)]
    return samples, context


@pytest.mark.parametrize('exercise', DETECTORS)
@pytest.mark.parametrize('case', FIXTURE['cases'])
def test_synthetic_cases(exercise, case):
    samples, context = build(exercise, case)
    result = DETECTORS[exercise](samples, context)
    expected = FIXTURE['cases'][case]
    assert result['detected'] == expected['detected']
    assert result['reason'] == expected['reason']
    assert result['fault_id'] == EXPERIMENTS[exercise].fault
    assert result['confidence'] == (.6 if result['detected'] else 0.)
    if result['detected']:
        assert 1 <= result['timestamp_start'] < result['timestamp_end'] <= 1.4
    else:
        assert result['timestamp_start'] is result['timestamp_end'] is None


@pytest.mark.parametrize('exercise', DETECTORS)
@pytest.mark.parametrize('change,reason', [
    ({'view': 'front'}, 'excluded_view_or_variant'),
    ({'variant': 'other'}, 'excluded_view_or_variant'),
    ({'phase_reviewed': False}, 'independent_phase_required'),
    ({'calibration_reviewed': False}, 'reviewed_calibration_required'),
    ({'geometry_verified': False}, 'geometry_not_verified'),
    ({'adapted_range': True}, 'adapted_range_excluded'),
])
def test_required_context(exercise, change, reason):
    samples, context = build(exercise)
    result = DETECTORS[exercise](samples, replace(context, **change))
    assert not result['detected'] and result['reason'] == reason


@pytest.mark.parametrize('exercise', DETECTORS)
@pytest.mark.parametrize('problem,reason', [
    ('gap', 'temporal_gap'), ('conflict', 'conflicting_duplicate'),
    ('reversed', 'non_monotonic_time'), ('nan', 'missing_or_invalid_metric'),
    ('quality', 'insufficient_pose_quality'), ('side', 'visible_side_changed'),
])
def test_input_corruption(exercise, problem, reason):
    samples, context = build(exercise)
    if problem == 'gap': samples.pop(2)
    if problem == 'conflict': samples.insert(1, {**samples[0], 'pose_confidence': .85})
    if problem == 'reversed': samples.reverse()
    if problem == 'nan': samples[2][EXPERIMENTS[exercise].metric] = float('nan')
    if problem == 'quality': samples[2]['pose_confidence'] = .6
    if problem == 'side': samples[2]['active_side'] = 'left'
    result = DETECTORS[exercise](samples, context)
    # Arm quality rejects a one-sided averaged metric before the side change gate.
    if problem == 'side' and EXPERIMENTS[exercise].metric == 'elbow_angle':
        reason = 'bilateral_arm_quality_required'
    assert not result['detected'] and result['reason'] == reason


@pytest.mark.parametrize('exercise', DETECTORS)
def test_duplicates_do_not_strengthen_evidence(exercise):
    samples, context = build(exercise)
    expected = DETECTORS[exercise](samples, context)
    duplicated = [sample for sample in samples for _ in range(4)]
    assert DETECTORS[exercise](duplicated, context) == expected


@pytest.mark.parametrize('exercise', DETECTORS)
def test_deficit_boundary_abstains(exercise):
    samples, context = build(exercise)
    for sample in samples: sample[EXPERIMENTS[exercise].metric] = 160
    assert not DETECTORS[exercise](samples, context)['detected']


@pytest.mark.parametrize('exercise', DETECTORS)
def test_raw_current_timeline_is_not_sufficient(exercise):
    samples, _ = build(exercise)
    for sample in samples: sample.pop('landmark_visibility')
    result = DETECTORS[exercise](samples, EvaluationContext(exercise_id=exercise, view='side', variant=EXPERIMENTS[exercise].variant))
    assert not result['detected'] and result['confidence'] == 0


def test_context_specific_gates():
    for exercise, field, value, reason in [
        ('handstand_push_up', 'inverted_body_ratio', .1, 'inverted_context_required'),
        ('thruster', 'wrist_lift', .01, 'overhead_context_required'),
        ('overhead_squat', 'wrist_lift', .01, 'overhead_context_required'),
    ]:
        samples, context = build(exercise)
        samples[2][field] = value
        assert DETECTORS[exercise](samples, context)['reason'] == reason


@pytest.mark.parametrize('exercise', DETECTORS)
def test_later_extension_peak_is_not_incomplete_final(exercise):
    samples, context = build(exercise)
    samples[2][EXPERIMENTS[exercise].metric] = 175
    assert not DETECTORS[exercise](samples, context)['detected']


@pytest.mark.parametrize('exercise', DETECTORS)
def test_incomplete_phase_coverage(exercise):
    samples, context = build(exercise)
    assert DETECTORS[exercise](samples[2:], context)['reason'] == 'incomplete_phase_coverage'


@pytest.mark.parametrize('exercise', DETECTORS)
def test_null_visibility_abstains(exercise):
    samples, context = build(exercise)
    samples[2]['landmark_visibility'] = None
    assert DETECTORS[exercise](samples, context)['reason'] == 'joint_visibility_required'


def test_experiments_are_not_imported_by_production():
    for file in [Path('app/main.py'), Path('app/services/analyzer.py'), Path('app/exercises.py')]:
        assert 'experimental_faults' not in file.read_text()
    library = json.loads(Path('app/services/exercise_library/exercises.json').read_text())
    assert all(not fault['detectable'] for item in library for fault in item['faults'])
