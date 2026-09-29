import pytest

from app import main
from app.services.exercise_validation import ExerciseMismatchError, validate_samples


def test_deadlift_rejects_a_clear_thruster_pattern():
    samples = [
        {"wrist_lift": 0.12, "knee_angle": 118.0},
        {"wrist_lift": 0.15, "knee_angle": 115.0},
        {"wrist_lift": 0.10, "knee_angle": 125.0},
    ]
    with pytest.raises(ExerciseMismatchError, match="Thruster"):
        validate_samples("Peso muerto", samples)


def test_deadlift_allows_a_hinge_without_overhead_extension():
    validate_samples("Peso muerto", [
        {"wrist_lift": 0.01, "knee_angle": 118.0},
        {"wrist_lift": 0.02, "knee_angle": 120.0},
        {"wrist_lift": 0.01, "knee_angle": 125.0},
    ])


def test_deadlift_rejects_a_clear_press_pattern_without_a_squat():
    with pytest.raises(ExerciseMismatchError, match="Press"):
        validate_samples("Peso muerto", [
            {"wrist_lift": 0.10, "knee_angle": 170.0},
            {"wrist_lift": 0.12, "knee_angle": 175.0},
            {"wrist_lift": 0.14, "knee_angle": 172.0},
        ])


def test_other_selected_exercises_are_not_reclassified_by_this_guard():
    validate_samples("Thruster", [
        {"wrist_lift": 0.15, "knee_angle": 110.0},
        {"wrist_lift": 0.15, "knee_angle": 110.0},
        {"wrist_lift": 0.15, "knee_angle": 110.0},
    ])


def test_mismatch_skips_full_analysis_and_ai_reasoning(client, monkeypatch):
    monkeypatch.setattr(main, "validate_video_exercise", lambda *_: (_ for _ in ()).throw(
        ExerciseMismatchError("El video presenta un patrón de Thruster")
    ))
    monkeypatch.setattr(main, "analyze_video", lambda *_args, **_kwargs: pytest.fail("No debe analizar"))
    monkeypatch.setattr(main, "_run_ai_reasoning", lambda *_args: pytest.fail("No debe usar OpenAI"))
    response = client.post(
        "/api/analyses", data={"exercise": "Peso muerto", "objective": "Técnica"},
        files={"file": ("thruster.mp4", b"video", "video/mp4")},
    )
    assert response.status_code == 202
    detail = client.get(f"/api/analyses/{response.json()['id']}").json()
    assert detail["status"] == "FAILED"
    assert "Thruster" in detail["error"]
