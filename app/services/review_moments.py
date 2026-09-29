"""Deterministic ranking of the first moments a coach should inspect."""
from __future__ import annotations
import os

def rank_review_moments(result: dict, observations: list[dict] | None = None) -> list[dict]:
    candidates = []
    reps = result.get("repetitions") or []
    for metric, title, direction in (("max_trunk_from_vertical", "Mayor inclinación del tronco", "high"), ("min_knee_angle", "Menor profundidad", "high")):
        values = [float(rep[metric]) for rep in reps if rep.get(metric) is not None]
        if len(values) < 2 or max(values) == min(values): continue
        mean = sum(values) / len(values)
        for rep in reps:
            if rep.get(metric) is None: continue
            value = float(rep[metric])
            deviation = (value - mean) if direction == "high" else (mean - value)
            if deviation <= 0: continue
            score = min(.9, .45 + deviation / max(max(values)-min(values), 1) * .45)
            candidates.append({"repetition_number": rep.get("repetition"), "timestamp": rep.get("bottom_s", rep.get("start_s", 0)), "title": title, "description": f"La repetición se aleja del promedio en {metric.replace('_', ' ')}.", "reason": "Desviación respecto del promedio de repeticiones.", "confidence": "medium", "priority_score": score})
    for observation in observations or []:
        if observation.get("timestamp") is None: continue
        severity = observation.get("severity", "review")
        score = {"priority": .95, "review": .8, "info": .6}.get(severity, .6)
        candidates.append({"repetition_number": observation.get("repetition"), "timestamp": observation["timestamp"], "title": observation.get("title", "Momento para revisar"), "description": observation.get("description", "Observación automática."), "reason": "Observación generada por razonamiento IA.", "confidence": observation.get("confidence", "medium"), "priority_score": score})
    window = float(os.getenv("AI_REVIEW_MOMENT_WINDOW_S", "1.5")); maximum = min(3, int(os.getenv("AI_REVIEW_MOMENTS_MAX", "3")))
    selected = []
    for item in sorted(candidates, key=lambda candidate: candidate["priority_score"], reverse=True):
        if any(abs(item["timestamp"] - chosen["timestamp"]) <= window for chosen in selected): continue
        selected.append(item)
        if len(selected) == maximum: break
    return selected
