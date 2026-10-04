"""Offline experiments only. Never imported by analyzer, API or feedback code.

Existing timeline metrics alone cannot establish phase, calibration or joint quality.
Callers must explicitly provide reviewed context and original pose visibility.
Confidence is an uncalibrated signal score, not a probability of technical error.
"""
from dataclasses import dataclass
import math
from typing import Any


@dataclass(frozen=True)
class EvaluationContext:
    exercise_id: str
    view: str
    variant: str = ''
    phase: str = ''
    phase_start: float | None = None
    phase_end: float | None = None
    phase_reviewed: bool = False
    complete_attempt: bool = False
    calibration_angle: float | None = None
    calibration_reviewed: bool = False
    geometry_verified: bool = False
    adapted_range: bool = False


@dataclass(frozen=True)
class Experiment:
    exercise: str
    fault: str
    metric: str
    phase: str
    variant: str
    joints: tuple[int, ...]
    duration: float = .25


EXPERIMENTS = {
    'deadlift': Experiment('deadlift', 'incomplete_hip_extension', 'hip_angle', 'final_extension', 'conventional', (11, 23, 25)),
    'air_squat': Experiment('air_squat', 'incomplete_knee_extension', 'knee_angle', 'final_extension', 'standard', (23, 25, 27)),
    'handstand_push_up': Experiment('handstand_push_up', 'incomplete_elbow_lockout', 'elbow_angle', 'final_lockout', 'strict', (11, 13, 15, 23, 27)),
    'thruster': Experiment('thruster', 'incomplete_elbow_lockout', 'elbow_angle', 'final_lockout', 'barbell', (11, 13, 15, 23, 25, 27)),
    'overhead_squat': Experiment('overhead_squat', 'sustained_elbow_flexion', 'elbow_angle', 'overhead_squat', 'barbell', (11, 13, 15, 23, 25, 27)),
}


def _finite(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _evaluate(samples: list[dict[str, Any]], context: EvaluationContext, spec: Experiment):
    evidence = {'exercise_id': spec.exercise, 'metric': spec.metric,
                'experimental': True, 'confidence_kind': 'uncalibrated_signal_score',
                'initial_deficit_deg': 10, 'uncertainty_deg': 5,
                'minimum_duration_s': spec.duration, 'minimum_samples': 3}

    def result(reason, detected=False, confidence=0., start=None, end=None):
        return {'fault_id': spec.fault, 'detected': detected, 'confidence': confidence,
                'timestamp_start': start, 'timestamp_end': end,
                'evidence': dict(evidence), 'reason': reason}

    if context.exercise_id != spec.exercise:
        return result('wrong_exercise')
    if context.view not in ('side', 'lateral') or context.variant != spec.variant:
        return result('excluded_view_or_variant')
    if context.adapted_range:
        return result('adapted_range_excluded')
    if not context.complete_attempt:
        return result('incomplete_attempt')
    if (not context.phase_reviewed or context.phase != spec.phase
            or not _finite(context.phase_start) or not _finite(context.phase_end)
            or context.phase_start < 0 or context.phase_end <= context.phase_start):
        return result('independent_phase_required')
    if (not context.calibration_reviewed or not _finite(context.calibration_angle)
            or not 150 <= context.calibration_angle <= 180):
        return result('reviewed_calibration_required')
    if not context.geometry_verified:
        return result('geometry_not_verified')
    evidence['calibration_angle'] = context.calibration_angle
    evidence['candidate_threshold_angle'] = context.calibration_angle - 15
    evidence['reviewed_phase_window'] = [context.phase_start, context.phase_end]

    # Reject conflicting duplicate frames; identical frames cannot extend duration.
    unique = []
    for sample in samples:
        if not isinstance(sample, dict):
            return result('invalid_sample')
        time = sample.get('time_s')
        if not _finite(time) or time < 0:
            return result('invalid_time')
        if unique and time < unique[-1]['time_s']:
            return result('non_monotonic_time')
        if unique and time == unique[-1]['time_s']:
            if sample != unique[-1]:
                return result('conflicting_duplicate')
            continue
        unique.append(sample)
    window = [sample for sample in unique if context.phase_start <= sample['time_s'] <= context.phase_end]
    evidence['samples_in_window'] = len(window)
    if len(window) < 3:
        return result('insufficient_samples')
    if window[0]['time_s'] - context.phase_start > .12 or context.phase_end - window[-1]['time_s'] > .12:
        return result('incomplete_phase_coverage')
    if any(b['time_s'] - a['time_s'] > .12 for a, b in zip(window, window[1:])):
        return result('temporal_gap')

    sides = set()
    angles = []
    for sample in window:
        angle = sample.get(spec.metric)
        if not _finite(angle) or not 20 <= angle <= 180:
            return result('missing_or_invalid_metric')
        if not _finite(sample.get('pose_confidence')) or not .8 <= sample['pose_confidence'] <= 1:
            return result('insufficient_pose_quality')
        side = sample.get('active_side')
        if side not in ('left', 'right', 'both'):
            return result('unknown_visible_side')
        sides.add(side)
        # Original landmark visibility, absent from saved production timelines.
        visibility = sample.get('landmark_visibility', {})
        if not isinstance(visibility, dict):
            return result('joint_visibility_required')
        indexes = spec.joints if side == 'left' else tuple(i + 1 for i in spec.joints)
        if side == 'both':
            indexes = spec.joints + tuple(i + 1 for i in spec.joints)
        if any(not _finite(visibility.get(str(i))) or not .75 <= visibility[str(i)] <= 1 for i in indexes):
            return result('joint_visibility_required')
        if spec.metric == 'elbow_angle' and side != 'both':
            # Current metric averages all valid arms, independently of active leg side.
            return result('bilateral_arm_quality_required')
        if spec.exercise == 'handstand_push_up':
            ratio = sample.get('inverted_body_ratio')
            if not _finite(ratio) or ratio < .5:
                return result('inverted_context_required')
        if spec.exercise in ('thruster', 'overhead_squat'):
            lift = sample.get('wrist_lift')
            if not _finite(lift) or lift < .08:
                return result('overhead_context_required')
        angles.append(angle)
    if len(sides) != 1:
        return result('visible_side_changed')
    deficits = [context.calibration_angle - angle for angle in angles]
    evidence.update(min_angle=min(angles), max_angle=max(angles),
                    min_deficit_deg=min(deficits), max_deficit_deg=max(deficits))
    if window[-1]['time_s'] - window[0]['time_s'] < spec.duration - 1e-9:
        return result('insufficient_duration')

    if spec.exercise == 'overhead_squat':
        # Only a continuous run in the reviewed squat phase; never bridge noise/gaps.
        run = []
        for sample, deficit in zip(window, deficits):
            run = run + [sample] if deficit > 15 else []
            if len(run) >= 3 and run[-1]['time_s'] - run[0]['time_s'] >= spec.duration - 1e-9:
                return result('sustained_deficit_candidate', True, .6, run[0]['time_s'], run[-1]['time_s'])
    elif min(deficits) > 15:
        # Final window must consistently lack extension; a later valid peak vetoes it.
        return result('sustained_deficit_candidate', True, .6, window[0]['time_s'], window[-1]['time_s'])
    if max(deficits) < 5:
        return result('no_deficit_observed')
    return result('borderline_or_unstable_signal')


def detect_deadlift_incomplete_hip_extension(samples, context):
    return _evaluate(samples, context, EXPERIMENTS['deadlift'])


def detect_air_squat_incomplete_knee_extension(samples, context):
    return _evaluate(samples, context, EXPERIMENTS['air_squat'])


def detect_hspu_strict_incomplete_elbow_lockout(samples, context):
    return _evaluate(samples, context, EXPERIMENTS['handstand_push_up'])


def detect_thruster_incomplete_elbow_lockout(samples, context):
    return _evaluate(samples, context, EXPERIMENTS['thruster'])


def detect_overhead_squat_sustained_elbow_flexion(samples, context):
    return _evaluate(samples, context, EXPERIMENTS['overhead_squat'])


DETECTORS = {
    'deadlift': detect_deadlift_incomplete_hip_extension,
    'air_squat': detect_air_squat_incomplete_knee_extension,
    'handstand_push_up': detect_hspu_strict_incomplete_elbow_lockout,
    'thruster': detect_thruster_incomplete_elbow_lockout,
    'overhead_squat': detect_overhead_squat_sustained_elbow_flexion,
}
