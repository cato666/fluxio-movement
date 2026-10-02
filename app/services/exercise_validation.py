"""Conservative preflight for video quality and exercise compatibility."""
from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

import cv2

from .analyzer import _pick_metrics, _press_metrics, ensure_model


class ExerciseMismatchError(ValueError):
    pass


class VideoQualityError(ValueError):
    pass


_ALIASES = {
    "squat": {"squat", "sentadilla", "back squat", "front squat"},
    "deadlift": {"deadlift", "peso muerto", "peso-muerto"},
    "press": {"press", "press militar", "overhead press", "shoulder press"},
    "thruster": {"thruster", "thrusters"},
    "clean": {"clean", "power clean"},
    "clean_and_jerk": {"clean and jerk", "clean & jerk", "clean jerks"},
    "snatch": {"snatch", "power snatch", "arrancada"},
    "other": {"otro", "other", "generico", "genérico"},
}


def _normalise(value: str) -> str:
    return " ".join((value or "").strip().casefold().split())


def _exercise_id(exercise: str) -> str:
    normalized = _normalise(exercise)
    return next((key for key, aliases in _ALIASES.items() if normalized in aliases), normalized)


@dataclass(frozen=True)
class VideoMetadata:
    width: int
    height: int
    fps: float
    frame_count: int

    @property
    def duration_s(self) -> float:
        return self.frame_count / self.fps if self.fps > 0 else 0.0


def _finite(value: Any) -> bool:
    return isinstance(value, (int, float)) and math.isfinite(float(value))


def quality_report(metadata: VideoMetadata, samples: list[dict[str, Any]]) -> dict[str, Any]:
    """Build a serialisable quality assessment from metadata and sparse pose samples."""
    sampled_frames = len(samples)
    full_body_frames = sum(
        all(_finite(sample.get(metric)) for metric in ("knee_angle", "hip_angle", "trunk_from_vertical"))
        for sample in samples
    )
    pose_coverage = round(full_body_frames / sampled_frames, 3) if sampled_frames else 0.0
    warnings: list[str] = []
    blockers: list[str] = []
    if metadata.width < 320 or metadata.height < 240:
        blockers.append("La resolución es demasiado baja. Usa al menos 320×240 px.")
    if metadata.fps < 10:
        blockers.append("El video tiene menos de 10 FPS. Usa un video más fluido.")
    if metadata.duration_s < 1:
        blockers.append("El video es demasiado corto para analizar un movimiento.")
    if sampled_frames < 3:
        blockers.append("No pudimos detectar una pose suficiente. Muestra el cuerpo completo y mejora la iluminación.")
    elif pose_coverage < 0.35:
        blockers.append("La pose se perdió en la mayor parte del video. Mantén hombros, caderas, rodillas y tobillos visibles.")
    elif pose_coverage < 0.65:
        warnings.append("La pose fue intermitente; el conteo de repeticiones puede requerir revisión humana.")
    if metadata.duration_s > 180:
        warnings.append("El video es largo; para mejor precisión, sube una serie de hasta 60 segundos.")
    return {
        "status": "FAILED" if blockers else "WARNING" if warnings else "PASSED",
        "resolution": [metadata.width, metadata.height], "fps": round(metadata.fps, 2),
        "duration_s": round(metadata.duration_s, 2), "sampled_pose_frames": sampled_frames,
        "full_body_pose_frames": full_body_frames, "pose_coverage": pose_coverage,
        "warnings": warnings, "blockers": blockers,
    }


def exercise_assessment(exercise: str, samples: list[dict[str, Any]]) -> dict[str, Any]:
    """Assess only unambiguous patterns; never guess complex Olympic lifts."""
    selected = _exercise_id(exercise)
    overhead = [s for s in samples if float(s.get("wrist_lift") or 0.0) >= 0.08]
    deep_knee = [s for s in samples if _finite(s.get("knee_angle")) and float(s["knee_angle"]) <= 130.0]
    very_deep_knee = [s for s in samples if _finite(s.get("knee_angle")) and float(s["knee_angle"]) <= 115.0]
    strong_hinge = [s for s in samples if _finite(s.get("hip_angle")) and float(s["hip_angle"]) <= 120.0]
    evidence = {"overhead_frames": len(overhead), "deep_knee_frames": len(deep_knee), "very_deep_knee_frames": len(very_deep_knee), "hinge_frames": len(strong_hinge)}
    detected: str | None = None
    if len(overhead) >= 3 and len(deep_knee) >= 3:
        detected = "thruster"
    elif len(overhead) >= 3 and len(deep_knee) < 3:
        detected = "press"
    elif len(very_deep_knee) >= 3 and len(strong_hinge) < 3:
        detected = "squat"
    # Body pose alone cannot safely distinguish Olympic lifts from their
    # visually similar overhead patterns. Keep those selections inconclusive.
    if selected in {"clean", "clean_and_jerk", "snatch"} and detected is not None:
        return {"status": "INCONCLUSIVE", "selected_exercise": selected, "detected_pattern": detected,
                "confidence": "low", "evidence": evidence,
                "message": "La pose corporal no alcanza para validar este levantamiento olímpico; se analizará usando la selección indicada."}
    if detected is not None and selected not in {detected, "other"}:
        label = {"press": "Press", "thruster": "Thruster", "squat": "Sentadilla"}[detected]
        return {"status": "MISMATCH", "selected_exercise": selected, "detected_pattern": detected,
                "confidence": "high", "evidence": evidence,
                "message": f"El video presenta un patrón claro de {label}, no de {exercise}. Selecciona {label} u otro ejercicio antes de analizar."}
    if detected is None:
        return {"status": "INCONCLUSIVE", "selected_exercise": selected, "detected_pattern": None,
                "confidence": "low", "evidence": evidence,
                "message": "No hubo evidencia suficiente para validar automáticamente el ejercicio; se analizará usando la selección indicada."}
    return {"status": "MATCH", "selected_exercise": selected, "detected_pattern": detected,
            "confidence": "high", "evidence": evidence,
            "message": "El patrón observado es compatible con el ejercicio seleccionado."}


def validate_samples(exercise: str, samples: list[dict[str, Any]]) -> dict[str, Any]:
    assessment = exercise_assessment(exercise, samples)
    if assessment["status"] == "MISMATCH":
        raise ExerciseMismatchError(assessment["message"])
    return assessment


def validate_video_exercise(video_path: str, exercise: str, max_seconds: float = 20.0) -> dict[str, Any]:
    """Scan sparse pose frames before full analysis or an AI request."""
    capture = cv2.VideoCapture(video_path)
    if not capture.isOpened():
        return {"quality": {"status": "UNAVAILABLE", "warnings": ["No se pudo ejecutar el preflight; el decodificador validará el archivo."], "blockers": []}, "exercise": {"status": "INCONCLUSIVE", "confidence": "low"}}
    try:
        metadata = VideoMetadata(int(capture.get(cv2.CAP_PROP_FRAME_WIDTH) or 0), int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT) or 0), float(capture.get(cv2.CAP_PROP_FPS) or 0.0), int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0))
        if metadata.fps <= 0:
            raise VideoQualityError("No se pudo obtener la frecuencia de cuadros del video.")
        import mediapipe as mp
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision
        every = max(1, int(round(metadata.fps / 5)))
        options = vision.PoseLandmarkerOptions(base_options=python.BaseOptions(model_asset_path=ensure_model()), running_mode=vision.RunningMode.VIDEO, num_poses=1, min_pose_detection_confidence=0.55, min_pose_presence_confidence=0.55, min_tracking_confidence=0.55)
        samples: list[dict[str, Any]] = []
        with vision.PoseLandmarker.create_from_options(options) as landmarker:
            index = 0
            while index / metadata.fps <= max_seconds:
                ok, frame = capture.read()
                if not ok:
                    break
                if index % every == 0:
                    image = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                    result = landmarker.detect_for_video(image, int(index / metadata.fps * 1000))
                    if result.pose_landmarks:
                        landmarks = result.pose_landmarks[0]
                        xy = [(point.x, point.y, point.z) for point in landmarks]
                        selected, _, _ = _pick_metrics(landmarks, xy)
                        press = _press_metrics(landmarks, xy)
                        sample: dict[str, Any] = {}
                        if selected is not None:
                            sample.update(selected[1])
                        if press is not None:
                            sample.update(press)
                        if sample:
                            samples.append(sample)
                index += 1
        quality = quality_report(metadata, samples)
        if quality["status"] == "FAILED":
            raise VideoQualityError(" ".join(quality["blockers"]))
        return {"quality": quality, "exercise": validate_samples(exercise, samples)}
    finally:
        capture.release()
