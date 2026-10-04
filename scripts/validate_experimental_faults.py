"""Replay local videos with the installed pose model; no downloads or production writes."""
import hashlib
import json
from pathlib import Path

import cv2
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from app.services.analyzer import _pick_metrics, _press_metrics, _pose_quality, _model_path
from app.services.experimental_faults import DETECTORS, EXPERIMENTS, EvaluationContext


def main():
    model = _model_path()
    if not model.is_file():
        raise RuntimeError('Existing pose model required; downloading is disabled')
    paths = sorted(Path('uploads').glob('*.mp4')) + sorted(Path('app/static').glob('*.mp4'))
    grouped = {}
    for path in paths:
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        grouped.setdefault(digest, []).append(path)
    records = []
    for digest, sources in grouped.items():
        path = sources[0]
        cap = cv2.VideoCapture(str(path))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        samples = []
        decoded = 0
        options = vision.PoseLandmarkerOptions(
            base_options=python.BaseOptions(model_asset_path=str(model)),
            running_mode=vision.RunningMode.VIDEO)
        if fps > 0:
            with vision.PoseLandmarker.create_from_options(options) as detector:
                stride = max(1, round(fps / 15))
                while True:
                    ok, frame = cap.read()
                    if not ok: break
                    index = decoded
                    decoded += 1
                    if index % stride: continue
                    time = index / fps
                    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pose = detector.detect_for_video(mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb), round(time * 1000))
                    if not pose.pose_landmarks: continue
                    landmarks = pose.pose_landmarks[0]
                    xy = [(p.x, p.y, p.z) for p in landmarks]
                    selected, left, right = _pick_metrics(landmarks, xy)
                    press = _press_metrics(landmarks, xy)
                    confidence, valid = _pose_quality(landmarks, None)
                    if not valid or (selected is None and press is None): continue
                    sample = dict(time_s=round(time, 3), pose_confidence=confidence,
                                  active_side=selected[0] if selected else 'arms',
                                  landmark_visibility={str(i): float(p.visibility or 0) for i, p in enumerate(landmarks)})
                    if selected: sample.update(selected[1])
                    if press: sample.update(press)
                    samples.append(sample)
        cap.release()
        outcomes = {}
        for exercise, detect in DETECTORS.items():
            # Hypothesis under test, not an assertion of video identity or phase.
            context = EvaluationContext(exercise_id=exercise, view='side', variant=EXPERIMENTS[exercise].variant)
            outcome = detect(samples, context)
            outcome['evidence'].update(video_exercise_confirmed=False,
                                       expected_result='UNLABELED', pose_samples=len(samples),
                                       missing_context=['reviewed exercise/view/variant', 'complete attempt',
                                                        'independent phase window', 'reviewed calibration', 'verified geometry'])
            outcomes[exercise] = outcome
        records.append(dict(sources=[str(p) for p in sources], sha256=digest,
                            decoded_frames=decoded, fps=fps, resolution=[width, height],
                            sample_time_range=[samples[0]['time_s'], samples[-1]['time_s']] if samples else None,
                            metrics_present=sorted({k for s in samples for k in s if k != 'landmark_visibility'}),
                            outcomes=outcomes))
    output = Path('results/experimental-faults/local-validation.json')
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({'model_sha256': hashlib.sha256(model.read_bytes()).hexdigest(),
                                  'confidence_kind': 'uncalibrated_signal_score', 'records': records}, indent=2), encoding='utf-8')
    print(f'{len(paths)} files; {len(records)} unique videos; {sum(r["decoded_frames"] for r in records)} decoded frames; output={output}')


if __name__ == '__main__':
    main()
