from __future__ import annotations

import json
import os
import subprocess
import urllib.request
from pathlib import Path

import cv2
import numpy as np

from .biomechanics import side_metrics
from .exercise_profiles import ExerciseProfileLoader, RepDetector, UnknownExerciseProfileError

MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"

CONNECTIONS = [
    (11, 12),
    (11, 13), (13, 15),
    (12, 14), (14, 16),
    (11, 23), (12, 24),
    (23, 24),
    (23, 25), (25, 27),
    (24, 26), (26, 28),
    (27, 29), (29, 31),
    (28, 30), (30, 32),
]

LANDMARK_GROUPS = {
    "shoulder": (11, 12), "elbow": (13, 14), "wrist": (15, 16),
    "hip": (23, 24), "knee": (25, 26), "ankle": (27, 28),
}


def _pose_quality(landmarks, profile):
    """Confidence for the landmarks a profile actually needs."""
    names = profile.required_landmarks if profile is not None else ("shoulder", "hip", "knee", "ankle")
    values = []
    for name in names:
        indexes = LANDMARK_GROUPS.get(name, ())
        if indexes:
            values.append(max(float(landmarks[index].visibility or 0.0) for index in indexes))
    confidence = sum(values) / len(values) if values else 0.0
    return round(confidence, 3), bool(values) and min(values) >= .55


def _model_path() -> Path:
    root = Path(__file__).resolve().parents[2]
    return root / "models" / "pose_landmarker_lite.task"


def ensure_model() -> str:
    path = _model_path()
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(MODEL_URL, path)
    return str(path)


def _smooth(values, window=9):
    arr = np.array(values, dtype=float)
    if len(arr) < window:
        return arr
    kernel = np.ones(window, dtype=float) / window
    return np.convolve(arr, kernel, mode="same")


def _valid_joint_angle(value, minimum=20.0, maximum=180.0):
    return value is not None and minimum <= float(value) <= maximum


def _side_visibility(landmarks, indexes):
    vals = []
    for i in indexes:
        visibility = landmarks[i].visibility
        vals.append(float(visibility) if visibility is not None else 0.0)
    return min(vals), sum(vals) / len(vals)


def _pick_metrics(lms, xy):
    """
    Calcula ambas piernas y usa una media cuando las dos son confiables.
    Esto reduce saltos falsos cuando MediaPipe cambia de lado visible.
    """
    left = side_metrics(xy, "left")
    right = side_metrics(xy, "right")

    left_min_vis, left_avg_vis = _side_visibility(lms, [11, 23, 25, 27])
    right_min_vis, right_avg_vis = _side_visibility(lms, [12, 24, 26, 28])

    candidates = []

    if (
        left_min_vis >= 0.55
        and _valid_joint_angle(left["knee_angle"])
        and _valid_joint_angle(left["hip_angle"], 15.0, 180.0)
        and 0.0 <= float(left["trunk_from_vertical"]) <= 90.0
    ):
        candidates.append(("left", left, left_avg_vis))

    if (
        right_min_vis >= 0.55
        and _valid_joint_angle(right["knee_angle"])
        and _valid_joint_angle(right["hip_angle"], 15.0, 180.0)
        and 0.0 <= float(right["trunk_from_vertical"]) <= 90.0
    ):
        candidates.append(("right", right, right_avg_vis))

    if not candidates:
        return None, left, right

    if len(candidates) == 2:
        _, lm, _ = candidates[0]
        _, rm, _ = candidates[1]
        merged = {
            "knee_angle": round((lm["knee_angle"] + rm["knee_angle"]) / 2.0, 1),
            "hip_angle": round((lm["hip_angle"] + rm["hip_angle"]) / 2.0, 1),
            "trunk_from_vertical": round(
                (lm["trunk_from_vertical"] + rm["trunk_from_vertical"]) / 2.0, 1
            ),
        }
        return ("both", merged), left, right

    side, metrics, _ = candidates[0]
    return (side, metrics), left, right


def _segment_reps(times, knee_angles):
    """
    MVP genérico para movimientos con flexión de rodilla.

    1. interpola huecos pequeños;
    2. busca mínimos locales significativos;
    3. genera una ventana por evento;
    4. fusiona eventos que pertenecen a la misma repetición.

    La fusión evita contar por separado la recepción y el dip/jerk de un
    levantamiento olímpico cuando ocurren dentro de la misma secuencia.
    """
    vals = np.array(
        [float(v) if v is not None else np.nan for v in knee_angles], dtype=float
    )

    if np.sum(~np.isnan(vals)) < 8:
        return []

    ids = np.arange(len(vals))
    valid = ~np.isnan(vals)
    vals = np.interp(ids, ids[valid], vals[valid])
    vals = _smooth(vals, 9)

    minima = []
    for i in range(2, len(vals) - 2):
        local_min = (
            vals[i] <= vals[i - 1]
            and vals[i] <= vals[i + 1]
            and vals[i] <= vals[i - 2]
            and vals[i] <= vals[i + 2]
        )

        if not local_min or vals[i] >= 130:
            continue

        if not minima or times[i] - times[minima[-1]] >= 1.0:
            minima.append(i)
        elif vals[i] < vals[minima[-1]]:
            minima[-1] = i

    raw = []
    for mi in minima:
        start = mi
        while (
            start > 0
            and times[mi] - times[start] < 3.0
            and vals[start] < 158
        ):
            start -= 1

        end = mi
        while (
            end < len(vals) - 1
            and times[end] - times[mi] < 3.0
            and vals[end] < 158
        ):
            end += 1

        raw.append(
            {
                "start_idx": start,
                "bottom_idx": mi,
                "end_idx": end,
                "min_knee_angle": float(vals[mi]),
            }
        )

    if not raw:
        return []

    # Fusiona ventanas muy solapadas o eventos cercanos dentro del mismo gesto.
    merged = []
    for item in raw:
        if not merged:
            merged.append(item)
            continue

        prev = merged[-1]
        prev_end_t = times[prev["end_idx"]]
        this_start_t = times[item["start_idx"]]
        bottom_gap = times[item["bottom_idx"]] - times[prev["bottom_idx"]]

        overlaps = this_start_t <= prev_end_t
        same_complex_rep = bottom_gap < 4.5

        if overlaps or same_complex_rep:
            prev["start_idx"] = min(prev["start_idx"], item["start_idx"])
            prev["end_idx"] = max(prev["end_idx"], item["end_idx"])
            if item["min_knee_angle"] < prev["min_knee_angle"]:
                prev["bottom_idx"] = item["bottom_idx"]
                prev["min_knee_angle"] = item["min_knee_angle"]
        else:
            merged.append(item)

    reps = []
    for n, item in enumerate(merged, 1):
        reps.append(
            {
                "repetition": n,
                "start_s": round(float(times[item["start_idx"]]), 2),
                "bottom_s": round(float(times[item["bottom_idx"]]), 2),
                "end_s": round(float(times[item["end_idx"]]), 2),
                "min_knee_angle": round(float(item["min_knee_angle"]), 1),
            }
        )

    return reps


def _joint_angle(a, b, c):
    """Ángulo en b para tres puntos normalizados de MediaPipe."""
    first = np.array(a[:2], dtype=float) - np.array(b[:2], dtype=float)
    second = np.array(c[:2], dtype=float) - np.array(b[:2], dtype=float)
    denominator = np.linalg.norm(first) * np.linalg.norm(second)
    if denominator == 0:
        return None
    cosine = np.clip(np.dot(first, second) / denominator, -1.0, 1.0)
    return float(np.degrees(np.arccos(cosine)))


def _press_metrics(lms, xy):
    """Métricas de brazos para Press: extensión de codo y alzada de muñeca."""
    sides = []
    for shoulder, elbow, wrist in ((11, 13, 15), (12, 14, 16)):
        visibility = min(float(lms[i].visibility or 0.0) for i in (shoulder, elbow, wrist))
        angle = _joint_angle(xy[shoulder], xy[elbow], xy[wrist])
        if visibility >= 0.55 and angle is not None:
            # El eje y normalizado crece hacia abajo: positivo equivale a muñeca sobre hombro.
            lift = float(xy[shoulder][1] - xy[wrist][1])
            sides.append((angle, lift))
    if not sides:
        return None
    return {
        "elbow_angle": round(sum(value[0] for value in sides) / len(sides), 1),
        "wrist_lift": round(sum(value[1] for value in sides) / len(sides), 3),
    }


def _front_deadlift_metrics(lms, xy):
    """Pose-relative vertical wrist travel for a frontal deadlift view."""
    required = (11, 12, 23, 24, 15, 16)
    if min(float(lms[index].visibility or 0.0) for index in required) < 0.55:
        return None
    shoulder_y = (float(xy[11][1]) + float(xy[12][1])) / 2.0
    hip_y = (float(xy[23][1]) + float(xy[24][1])) / 2.0
    wrist_y = (float(xy[15][1]) + float(xy[16][1])) / 2.0
    torso_height = hip_y - shoulder_y
    if torso_height <= 0.03:
        return None
    return {"wrist_drop_ratio": round((wrist_y - hip_y) / torso_height, 3)}


def _segment_press_reps(times, elbow_angles, wrist_lifts):
    """Cuenta Press de barra de posición baja a bloqueo por extensión de codos."""
    reps = []
    lower_index = None
    for index, (elbow, lift) in enumerate(zip(elbow_angles, wrist_lifts)):
        if elbow is None or lift is None:
            continue
        # Durante la subida el codo puede seguir flexionado, pero la muñeca ya
        # dejó la posición de inicio. Ambas señales deben ser bajas para reiniciar.
        is_lower = elbow <= 145.0 and lift <= 0.04
        is_lockout = elbow >= 160.0 and lift >= 0.08
        if is_lower:
            lower_index = index
            continue
        if is_lockout and lower_index is not None:
            duration = times[index] - times[lower_index]
            if 0.15 <= duration <= 8.0:
                reps.append({
                    "repetition": len(reps) + 1,
                    "start_s": round(float(times[lower_index]), 2),
                    "bottom_s": round(float(times[lower_index]), 2),
                    "end_s": round(float(times[index]), 2),
                    "min_elbow_angle": round(float(elbow_angles[lower_index]), 1),
                    "lockout_elbow_angle": round(float(elbow), 1),
                })
                lower_index = None
    return reps


def _is_press(exercise):
    return (exercise or "").strip().casefold() in {"press", "press militar", "overhead press"}


def _profile_for_exercise(exercise: str | None, view: str):
    """Use profiles where they exist and retain legacy analysis for other MVP exercises."""
    if not exercise:
        return None
    try:
        return ExerciseProfileLoader().load(exercise, view)
    except UnknownExerciseProfileError:
        return None


def _encode_browser_video(temp_path: str, final_path: str):
    """Convierte el video de OpenCV a H.264/yuv420p reproducible en navegador."""
    cmd = [
        "ffmpeg",
        "-y",
        "-i", temp_path,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-pix_fmt", "yuv420p",
        "-movflags", "+faststart",
        "-an",
        final_path,
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f"FFmpeg no pudo convertir el video: {result.stderr[-1200:]}")

    if not os.path.exists(final_path) or os.path.getsize(final_path) == 0:
        raise RuntimeError("FFmpeg terminó, pero el video final quedó vacío")


def analyze_video(
    video_path: str, output_dir: str, exercise: str | None = None, view: str = "side",
    progress_callback=None,
):
    import mediapipe as mp
    from mediapipe.tasks import python
    from mediapipe.tasks.python import vision

    profile = _profile_for_exercise(exercise, view)
    model = ensure_model()
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        raise RuntimeError("No se pudo abrir el video")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    temp_annotated = str(out_dir / "annotated_temp.mp4")
    annotated = str(out_dir / "annotated.mp4")

    writer = cv2.VideoWriter(
        temp_annotated,
        cv2.VideoWriter_fourcc(*"mp4v"),
        fps,
        (width, height),
    )

    if not writer.isOpened():
        cap.release()
        raise RuntimeError("No se pudo crear el video anotado temporal")

    options = vision.PoseLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=model),
        running_mode=vision.RunningMode.VIDEO,
        num_poses=1,
        min_pose_detection_confidence=0.55,
        min_pose_presence_confidence=0.55,
        min_tracking_confidence=0.55,
    )

    timeline = []
    sample_every = max(1, int(round(fps / 15)))
    last_landmarks_px = None
    last_metrics = None
    last_progress = -1

    def report(progress, stage):
        if progress_callback is not None:
            progress_callback(progress, stage)

    try:
        with vision.PoseLandmarker.create_from_options(options) as landmarker:
            idx = 0

            while True:
                ok, frame = cap.read()
                if not ok:
                    break

                t = idx / fps
                progress = 8 + int((idx / max(total, 1)) * 70)
                if progress >= last_progress + 5:
                    report(progress, "analyzing")
                    last_progress = progress

                if idx % sample_every == 0:
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
                    result = landmarker.detect_for_video(mp_img, int(t * 1000))

                    last_landmarks_px = None
                    last_metrics = None

                    if result.pose_landmarks:
                        lms = result.pose_landmarks[0]
                        xy = [(p.x, p.y, p.z) for p in lms]

                        selected, left, right = _pick_metrics(lms, xy)
                        press = _press_metrics(lms, xy)
                        front_deadlift = _front_deadlift_metrics(lms, xy)

                        pose_confidence, required_landmarks_valid = _pose_quality(lms, profile)
                        if (selected is not None or press is not None or front_deadlift is not None) and required_landmarks_valid:
                            last_landmarks_px = [
                                (
                                    int(p.x * width),
                                    int(p.y * height),
                                    float(p.visibility or 0.0),
                                )
                                for p in lms
                            ]

                            if selected is not None:
                                active_side, metrics = selected
                                last_metrics = {
                                    "time_s": round(t, 3),
                                    "active_side": active_side,
                                    "left": left,
                                    "right": right,
                                    "knee_angle": metrics["knee_angle"],
                                    "hip_angle": metrics["hip_angle"],
                                    "trunk_from_vertical": metrics["trunk_from_vertical"],
                                }
                            else:
                                last_metrics = {
                                    "time_s": round(t, 3), "active_side": "arms",
                                    "left": left, "right": right,
                                    "knee_angle": None, "hip_angle": None,
                                    "trunk_from_vertical": None,
                                }
                            if press is not None:
                                last_metrics.update({
                                    "elbow_angle": press["elbow_angle"],
                                    "wrist_lift": press["wrist_lift"],
                                })
                            if front_deadlift is not None:
                                last_metrics.update(front_deadlift)
                            last_metrics["pose_confidence"] = pose_confidence
                            timeline.append(last_metrics)

                if last_landmarks_px:
                    for a, b in CONNECTIONS:
                        if (
                            a < len(last_landmarks_px)
                            and b < len(last_landmarks_px)
                            and last_landmarks_px[a][2] >= 0.45
                            and last_landmarks_px[b][2] >= 0.45
                        ):
                            cv2.line(
                                frame,
                                last_landmarks_px[a][:2],
                                last_landmarks_px[b][:2],
                                (255, 255, 255),
                                2,
                            )

                    for x, y, visibility in last_landmarks_px:
                        if visibility >= 0.45:
                            cv2.circle(frame, (x, y), 4, (255, 255, 255), -1)

                if last_metrics:
                    cv2.rectangle(frame, (12, 12), (360, 128), (0, 0, 0), -1)
                    cv2.putText(
                        frame,
                        f"Knee {last_metrics['knee_angle']} deg",
                        (20, 42),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.72,
                        (255, 255, 255),
                        2,
                    )
                    cv2.putText(
                        frame,
                        f"Hip {last_metrics['hip_angle']} deg",
                        (20, 76),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.72,
                        (255, 255, 255),
                        2,
                    )
                    cv2.putText(
                        frame,
                        f"Trunk {last_metrics['trunk_from_vertical']} deg",
                        (20, 110),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.72,
                        (255, 255, 255),
                        2,
                    )

                writer.write(frame)
                idx += 1

    finally:
        cap.release()
        writer.release()

    report(82, "annotating")
    _encode_browser_video(temp_annotated, annotated)
    report(95, "finalizing")

    try:
        os.remove(temp_annotated)
    except OSError:
        pass

    times = [x["time_s"] for x in timeline]
    knees = [x["knee_angle"] for x in timeline]
    if profile is not None:
        reps = RepDetector(profile).detect(timeline)
    else:
        reps = _segment_reps(times, knees) if timeline else []

    valid = [
        x
        for x in timeline
        if _valid_joint_angle(x.get("knee_angle"))
        and _valid_joint_angle(x.get("hip_angle"), 15.0, 180.0)
        and x.get("trunk_from_vertical") is not None
        and 0.0 <= float(x["trunk_from_vertical"]) <= 90.0
    ]
    pose_confidences = [float(x["pose_confidence"]) for x in timeline if x.get("pose_confidence") is not None]
    average_pose_confidence = round(sum(pose_confidences) / len(pose_confidences), 2) if pose_confidences else 0.0
    repetition_confidences = [rep.get("count_confidence") for rep in reps]
    count_confidence = (
        "high" if repetition_confidences and all(value == "high" for value in repetition_confidences)
        else "medium" if repetition_confidences and any(value in {"high", "medium"} for value in repetition_confidences)
        else "low"
    )

    summary = {
        "video": {
            "fps": round(fps, 2),
            "frames": total,
            "duration_s": round(total / fps, 2) if fps else None,
            "resolution": [width, height],
        },
        "pose_frames": len(timeline),
        "pose_quality": {
            "average_confidence": average_pose_confidence,
            "valid_samples": len(timeline),
            "confidence": "high" if average_pose_confidence >= .8 else "medium" if average_pose_confidence >= .65 else "low",
        },
        "repetition_count_confidence": count_confidence,
        "exercise_profile": {
            "id": profile.id,
            "version": profile.version,
            "view": view,
            "supported_views": list(profile.views),
        } if profile is not None else None,
        "repetitions_detected": len(reps),
        "repetitions": reps,
        "summary_metrics": {
            "min_knee_angle": round(
                min((x["knee_angle"] for x in valid), default=0.0), 1
            ) if valid else None,
            "min_hip_angle": round(
                min((x["hip_angle"] for x in valid), default=0.0), 1
            ) if valid else None,
            "max_trunk_from_vertical": round(
                max((x["trunk_from_vertical"] for x in valid), default=0.0), 1
            ) if valid else None,
        },
        "timeline": timeline,
        "notes": [
            "MVP técnico: métricas 2D dependientes del ángulo de cámara.",
            "Se filtran landmarks de baja visibilidad y ángulos no plausibles.",
            "Los eventos cercanos se fusionan para reducir repeticiones duplicadas.",
            "Los perfiles configurados usan señales específicas de cada ejercicio para detectar repeticiones.",
            "No reemplaza evaluación profesional o clínica.",
        ],
    }

    (out_dir / "analysis.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return summary
