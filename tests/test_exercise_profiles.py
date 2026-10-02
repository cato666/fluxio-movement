import pytest

from app.services.exercise_profiles import (
    ExerciseProfileLoader,
    RepDetector,
    UnknownExerciseProfileError,
    UnsupportedViewError,
)


def samples(signal, metric, values, start=0.0, step=0.1):
    return [
        {"time_s": round(start + index * step, 2), signal: value, "knee_angle": value if signal == "knee_angle" else 150.0,
         "hip_angle": value if signal == "hip_angle" else 150.0, "trunk_from_vertical": 15.0}
        for index, value in enumerate(values)
    ]


def detect(exercise, signal, values):
    profile = ExerciseProfileLoader().load(exercise, "side")
    return RepDetector(profile).detect(samples(signal, signal, values))


def test_squat_profile_detects_known_complete_repetitions():
    reps = detect("Sentadilla", "knee_angle", [165, 165, 140, 140, 95, 95, 140, 140, 165, 165])
    assert len(reps) == 1
    assert reps[0]["profile"] == "squat-side"
    assert reps[0]["bottom_s"] == 0.5


def test_deadlift_profile_detects_known_complete_repetitions():
    reps = detect("Peso muerto", "hip_angle", [165, 165, 105, 105, 150, 150, 165, 165])
    assert len(reps) == 1
    assert reps[0]["profile"] == "deadlift-side"
    assert reps[0]["bottom_s"] == 0.3


def test_deadlift_front_profile_detects_wrist_travel_cycles():
    profile = ExerciseProfileLoader().load("Peso muerto", "front")
    sequence = [
        {"time_s": index * 0.1, "wrist_drop_ratio": value, "knee_angle": 150.0, "hip_angle": 150.0, "trunk_from_vertical": 15.0}
        for index, value in enumerate([0.0, 0.0, 0.6, 0.6, 0.9, 0.9, 0.3, 0.3, 0.0, 0.0])
    ]
    reps = RepDetector(profile).detect(sequence)
    assert profile.id == "deadlift-front"
    assert len(reps) == 1
    assert reps[0]["profile"] == "deadlift-front"


def test_clean_profile_requires_the_full_pull_receive_and_stand_sequence():
    reps = detect("Clean", "knee_angle", [160, 160, 120, 120, 155, 155, 105, 105, 160, 160])
    assert len(reps) == 1
    assert reps[0]["profile"] == "clean-side"
    assert reps[0]["bottom_s"] == 0.7


def test_snatch_profile_detects_the_full_pull_receive_and_stand_sequence():
    reps = detect("Snatch", "knee_angle", [165, 165, 135, 135, 160, 160, 120, 120, 165, 165])
    assert len(reps) == 1
    assert reps[0]["profile"] == "snatch-side"


def test_press_profile_detects_low_to_lockout_cycles():
    profile = ExerciseProfileLoader().load("Press", "side")
    sequence = [
        {"time_s": 0.0, "wrist_lift": 0.01, "elbow_angle": 130.0},
        {"time_s": 0.1, "wrist_lift": 0.01, "elbow_angle": 130.0},
        {"time_s": 0.2, "wrist_lift": 0.05, "elbow_angle": 145.0},
        {"time_s": 0.3, "wrist_lift": 0.05, "elbow_angle": 145.0},
        {"time_s": 0.4, "wrist_lift": 0.10, "elbow_angle": 165.0},
        {"time_s": 0.5, "wrist_lift": 0.10, "elbow_angle": 165.0},
    ]
    reps = RepDetector(profile).detect(sequence)
    assert len(reps) == 1
    assert reps[0]["profile"] == "press-side"


def test_thruster_profile_requires_squat_drive_and_overhead_lockout():
    profile = ExerciseProfileLoader().load("Thruster", "side")
    sequence = [
        {"time_s": index * 0.1, "knee_angle": knee, "hip_angle": 150.0, "trunk_from_vertical": 15.0,
         "wrist_lift": wrist, "elbow_angle": elbow}
        for index, (knee, wrist, elbow) in enumerate([
            (165, 0.01, 135), (165, 0.01, 135), (120, 0.01, 130), (120, 0.01, 130),
            (150, 0.04, 145), (150, 0.04, 145), (160, 0.10, 165), (160, 0.10, 165),
        ])
    ]
    reps = RepDetector(profile).detect(sequence)
    assert len(reps) == 1
    assert reps[0]["profile"] == "thruster-side"


def test_thruster_does_not_count_a_squat_without_overhead_lockout():
    profile = ExerciseProfileLoader().load("Thruster", "side")
    sequence = [
        {"time_s": index * 0.1, "knee_angle": knee, "hip_angle": 150.0, "trunk_from_vertical": 15.0,
         "wrist_lift": wrist, "elbow_angle": 145.0}
        for index, (knee, wrist) in enumerate([(165, .01), (165, .01), (120, .01), (120, .01), (150, .04), (150, .04), (160, .04), (160, .04)])
    ]
    assert RepDetector(profile).detect(sequence) == []


def test_other_profile_uses_the_generic_complete_lower_body_cycle():
    reps = detect("Otro", "knee_angle", [165, 165, 140, 140, 95, 95, 140, 140, 165, 165])
    assert len(reps) == 1
    assert reps[0]["profile"] == "other-side"


def test_detector_does_not_duplicate_a_rep_while_the_lifter_stays_at_lockout():
    reps = detect("squat-side", "knee_angle", [165, 165, 140, 140, 95, 95, 140, 140, 165, 165, 165, 165])
    assert len(reps) == 1


def test_detector_does_not_count_a_partial_sequence_as_a_repetition():
    reps = detect("squat-side", "knee_angle", [165, 165, 140, 140, 95, 95, 165, 165])
    assert reps == []


def test_detector_ignores_incomplete_pose_samples_and_tolerates_a_short_gap():
    profile = ExerciseProfileLoader().load("squat-side", "side")
    sequence = samples("knee_angle", "knee_angle", [165, 165, 140, 140, 95, 95, 140, 140, 165, 165])
    sequence.insert(5, {"time_s": 0.45, "knee_angle": None})
    reps = RepDetector(profile).detect(sequence)
    assert len(reps) == 1


def test_unknown_exercise_and_unsupported_view_are_rejected_by_the_loader():
    loader = ExerciseProfileLoader()
    with pytest.raises(UnknownExerciseProfileError):
        loader.load("Kettlebell swing", "side")
    with pytest.raises(UnsupportedViewError):
        loader.load("clean-side", "top")


def test_profiles_are_selected_per_view_and_expose_a_version():
    loader = ExerciseProfileLoader()
    assert loader.load("Sentadilla", "side").id == "squat-side"
    assert loader.load("Sentadilla", "front").id == "squat-front"
    assert loader.load("Clean & Jerk", "side").id == "clean-and-jerk-side"
    assert loader.load("Clean & Jerk", "front").id == "clean-and-jerk-front"
    assert loader.load("Clean and Jerk", "side").id == "clean-and-jerk-side"
    assert loader.load("Clean & Jerk", "side").version == "1.0"


def test_low_pose_confidence_does_not_complete_a_repetition():
    profile = ExerciseProfileLoader().load("Sentadilla", "side")
    sequence = samples("knee_angle", "knee_angle", [165, 165, 140, 140, 95, 95, 140, 140, 165, 165])
    for sample in sequence[2:8]:
        sample["pose_confidence"] = 0.4
    assert RepDetector(profile).detect(sequence) == []


def test_clean_and_jerk_requires_clean_then_jerk_lockout():
    profile = ExerciseProfileLoader().load("Clean & Jerk", "side")
    phases = [
        (165, .01), (165, .01), (120, .01), (120, .01),
        (155, .02), (155, .02), (110, .04), (110, .04),
        (160, .03), (160, .03), (140, .03), (140, .03),
        (157, .05), (157, .05), (160, .10), (160, .10),
    ]
    sequence = [
        {"time_s": index * .1, "knee_angle": knee, "hip_angle": 150.0,
         "trunk_from_vertical": 15.0, "wrist_lift": wrist, "elbow_angle": 165.0,
         "pose_confidence": .9}
        for index, (knee, wrist) in enumerate(phases)
    ]
    reps = RepDetector(profile).detect(sequence)
    assert len(reps) == 1
    assert reps[0]["profile"] == "clean-and-jerk-side"
    assert reps[0]["count_confidence"] == "high"


@pytest.mark.parametrize("exercise", ["Sentadilla", "Clean", "Press", "Thruster", "Snatch", "Otro"])
def test_configured_exercises_accept_front_and_side_views(exercise):
    loader = ExerciseProfileLoader()
    assert loader.load(exercise, "side").id
    assert loader.load(exercise, "front").id
