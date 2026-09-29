"""Small local preflight that rejects obvious exercise/profile mismatches."""
from __future__ import annotations

import cv2

from .analyzer import _pick_metrics, _press_metrics, ensure_model


class ExerciseMismatchError(ValueError):
    pass


_DEADLIFT_NAMES = {"deadlift", "peso muerto", "peso-muerto"}


def validate_samples(exercise: str, samples: list[dict]) -> None:
    """Raise only for high-confidence conflicts; inconclusive clips continue."""
    normalized = " ".join((exercise or "").strip().casefold().split())
    if normalized not in _DEADLIFT_NAMES:
        return
    overhead_frames = sum(sample.get("wrist_lift", 0.0) >= 0.08 for sample in samples)
    knee_dip_frames = sum(sample.get("knee_angle", 180.0) <= 130.0 for sample in samples)
    if overhead_frames >= 3:
        detected = "Thruster" if knee_dip_frames >= 3 else "Press"
        raise ExerciseMismatchError(
            f"El video presenta un patrón de {detected} con extensión sobre la cabeza, no de Peso muerto. "
            f"Selecciona {detected} u otro ejercicio antes de analizar."
        )


def validate_video_exercise(video_path: str, exercise: str, max_seconds: float = 20.0) -> None:
    """Scan a sparse set of pose frames before the full analysis or OpenAI call."""
    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        return
    try:
        import mediapipe as mp
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision

        fps = capture.get(cv2.CAP_PROP_FPS) or 30.0
        every = max(1, int(round(fps / 5)))
        options = vision.PoseLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=ensure_model()),
            running_mode=vision.RunningMode.VIDEO, num_poses=1,
            min_pose_detection_confidence=0.55, min_pose_presence_confidence=0.55,
            min_tracking_confidence=0.55,
        )
        samples: list[dict] = []
        with vision.PoseLandmarker.create_from_options(options) as landmarker:
            index = 0
            while index / fps <= max_seconds:
                ok, frame = capture.read()
                if not ok:
                    break
                if index % every == 0:
                    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    result = landmarker.detect_for_video(image, int(index / fps * 1000))
                    if result.pose_landmarks:
                        landmarks = result.pose_landmarks[0]
                        xy = [(point.x, point.y, point.z) for point in landmarks]
                        selected, _, _ = _pick_metrics(landmarks, xy)
                        press = _press_metrics(landmarks, xy)
                        sample = {}
                        if selected is not None:
                            sample.update(selected[1])
                        if press is not None:
                            sample.update(press)
                        if sample:
                            samples.append(sample)
                index += 1
        validate_samples(exercise, samples)
    finally:
        capture.release()
