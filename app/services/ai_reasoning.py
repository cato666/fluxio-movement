"""Small, optional OpenAI reasoning layer over deterministic video analysis."""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


SYSTEM_PROMPT = """Eres un asistente técnico para coaches deportivos. Basa cada observación exclusivamente en las métricas, eventos, perfil y comparaciones recibidas. No inventes mediciones, no diagnostiques lesiones ni des recomendaciones médicas. No declares una técnica correcta o incorrecta de forma absoluta: describe patrones observables y momentos que merecen revisión humana. El coach es la autoridad final.

Respeta `reasoning_eligibility`: si `can_generate_observations` es false, devuelve `observations: []` y un resumen breve que indique que la captura o las métricas no ofrecen evidencia suficiente. No rellenes observaciones por defecto.

Cada observación debe incluir `evidence`: una frase breve con al menos una métrica o timestamp numérico exacto recibido en el input. Explica la comparación o evento que sustenta la sugerencia. Si no puedes citar evidencia numérica concreta, no generes la observación. Máximo 5 observaciones breves."""

OBSERVATION_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["observations", "summary"],
    "properties": {
        "observations": {
            "type": "array", "maxItems": 5,
            "items": {"type": "object", "additionalProperties": False,
                "required": ["repetition", "timestamp", "category", "severity", "title", "description", "evidence", "confidence"],
                "properties": {
                    "repetition": {"anyOf": [{"type": "integer", "minimum": 1}, {"type": "null"}]},
                    "timestamp": {"anyOf": [{"type": "number", "minimum": 0}, {"type": "null"}]},
                    "category": {"type": "string", "maxLength": 80},
                    "severity": {"type": "string", "enum": ["info", "review", "priority"]},
                    "title": {"type": "string", "maxLength": 240},
                    "description": {"type": "string", "maxLength": 800},
                    "evidence": {"type": "string", "minLength": 3, "maxLength": 500},
                    "confidence": {"type": "string", "enum": ["low", "medium", "high"]},
                },
            },
        },
        "summary": {"type": "string", "maxLength": 800},
    },
}


@dataclass
class ReasoningResult:
    observations: list[dict]
    summary: str
    model: str
    usage: dict
    latency_ms: int


def enabled() -> bool:
    return os.getenv("AI_REASONING_ENABLED", "true").strip().casefold() in {"1", "true", "yes", "on"} and bool(os.getenv("OPENAI_API_KEY"))


METRIC_KEYS = (
    "min_knee_angle", "max_knee_angle", "min_hip_angle", "max_hip_angle",
    "min_trunk_from_vertical", "max_trunk_from_vertical", "min_elbow_angle",
    "max_elbow_angle", "lockout_elbow_angle", "min_wrist_lift", "max_wrist_lift",
)


def _confidence_is_low(value: object) -> bool:
    return value == "low" or (isinstance(value, (int, float)) and value < .65)


def build_input(exercise: str, view: str, result: dict) -> dict:
    repetitions = []
    for rep in (result.get("repetitions") or [])[:20]:
        metrics = {key: rep.get(key) for key in METRIC_KEYS if rep.get(key) is not None}
        repetitions.append({
            "number": rep.get("repetition"), "start_s": rep.get("start_s"),
            "bottom_s": rep.get("bottom_s"), "end_s": rep.get("end_s"),
            "profile": rep.get("profile"), "profile_version": rep.get("profile_version"),
            "pose_confidence": rep.get("pose_confidence"), "count_confidence": rep.get("count_confidence"),
            "metrics": metrics,
        })
    comparisons = {}
    for metric in ("min_knee_angle", "min_hip_angle", "max_trunk_from_vertical", "lockout_elbow_angle"):
        values = [rep["metrics"].get(metric) for rep in repetitions if rep["metrics"].get(metric) is not None]
        if len(values) > 1:
            comparisons[metric] = {"min": min(values), "max": max(values), "range": round(max(values) - min(values), 2)}
    pose_quality = result.get("pose_quality") or {}
    count_confidence = result.get("repetition_count_confidence")
    eligibility_reasons = []
    if not repetitions:
        eligibility_reasons.append("no_detected_repetitions")
    if not pose_quality:
        eligibility_reasons.append("pose_quality_unavailable")
    if not count_confidence:
        eligibility_reasons.append("count_confidence_unavailable")
    if _confidence_is_low(pose_quality.get("confidence")) or _confidence_is_low(pose_quality.get("average_confidence")):
        eligibility_reasons.append("low_pose_confidence")
    if _confidence_is_low(count_confidence):
        eligibility_reasons.append("low_count_confidence")
    return {
        "exercise": exercise, "view": view,
        "exercise_profile": result.get("exercise_profile") or {},
        "pose_quality": pose_quality,
        "repetition_count_confidence": count_confidence,
        "preflight": result.get("preflight") or {},
        "repetitions": repetitions,
        "metrics": result.get("summary_metrics") or {},
        "events": [
            {"repetition": rep["number"], "type": event_type, "timestamp_s": rep[timestamp_key]}
            for rep in repetitions
            for event_type, timestamp_key in (("start", "start_s"), ("bottom", "bottom_s"), ("end", "end_s"))
            if rep.get(timestamp_key) is not None
        ],
        "comparisons": comparisons,
        "reasoning_eligibility": {
            "can_generate_observations": not eligibility_reasons,
            "reasons": eligibility_reasons,
        },
    }


def _numeric_values(value: object) -> list[float]:
    if isinstance(value, dict):
        return [number for item in value.values() for number in _numeric_values(item)]
    if isinstance(value, list):
        return [number for item in value for number in _numeric_values(item)]
    return [float(value)] if isinstance(value, (int, float)) and not isinstance(value, bool) else []


def _has_grounded_numeric_evidence(evidence: object, compact_input: dict) -> bool:
    if not isinstance(evidence, str) or not evidence.strip():
        return False
    cited = [float(value.replace(",", ".")) for value in re.findall(r"-?\d+(?:[.,]\d+)?", evidence)]
    allowed = _numeric_values(compact_input)
    return bool(cited) and all(any(abs(value - source) <= .05 for source in allowed) for value in cited)


def _fallback_evidence(observation: dict, compact_input: dict) -> str | None:
    """Create a traceable numeric citation when the provider reformats a value.

    The provider may round or calculate a value in its prose. We never persist
    that value as evidence: we cite the underlying repetition values instead.
    """
    repetitions = compact_input.get("repetitions") or []
    repetition = next((item for item in repetitions if item.get("number") == observation.get("repetition")), None)
    if repetition is None and isinstance(observation.get("timestamp"), (int, float)):
        timestamp = float(observation["timestamp"])
        candidates = [
            (abs(float(value) - timestamp), item)
            for item in repetitions
            for value in (item.get("start_s"), item.get("bottom_s"), item.get("end_s"))
            if isinstance(value, (int, float))
        ]
        if candidates:
            repetition = min(candidates, key=lambda candidate: candidate[0])[1]
    if repetition is None:
        return None

    parts = [f"Rep {repetition['number']}"] if repetition.get("number") is not None else []
    for key in ("bottom_s", "start_s", "end_s"):
        value = repetition.get(key)
        if isinstance(value, (int, float)):
            parts.append(f"{key}: {float(value):.2f} s")
            break
    for key, value in repetition.get("metrics", {}).items():
        if isinstance(value, (int, float)):
            parts.append(f"{key}: {float(value):.1f}°")
            break
    return " · ".join(parts) if len(parts) >= 2 else None


def _output_text(response: dict) -> str:
    if response.get("output_text"):
        return response["output_text"]
    for item in response.get("output", []):
        for content in item.get("content", []):
            if content.get("type") == "output_text":
                return content.get("text", "")
    raise ValueError("OpenAI no devolvió texto estructurado")


def _request(payload: dict, api_key: str) -> dict:
    request = Request("https://api.openai.com/v1/responses", data=json.dumps(payload).encode(), headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}, method="POST")
    with urlopen(request, timeout=30) as response:
        return json.loads(response.read().decode())


def _unique_observations(observations: list[dict]) -> list[dict]:
    """Keep one copy of an equivalent suggestion returned by the model."""
    unique: list[dict] = []
    fingerprints: set[tuple] = set()
    for observation in observations:
        timestamp = observation.get("timestamp")
        fingerprint = (
            observation.get("repetition"),
            None if timestamp is None else round(float(timestamp), 1),
            " ".join(str(observation.get("title", "")).casefold().split()),
            " ".join(str(observation.get("description", "")).casefold().split()),
        )
        if fingerprint not in fingerprints:
            fingerprints.add(fingerprint)
            unique.append(observation)
    return unique


def run_reasoning(exercise: str, view: str, result: dict) -> ReasoningResult | None:
    if not enabled():
        return None
    model = os.getenv("AI_REASONING_MODEL", "gpt-5.6-terra")
    effort = os.getenv("AI_REASONING_EFFORT", "medium")
    compact_input = build_input(exercise, view, result)
    payload = {"model": model, "reasoning": {"effort": effort}, "input": [{"role": "system", "content": [{"type": "input_text", "text": SYSTEM_PROMPT}]}, {"role": "user", "content": [{"type": "input_text", "text": json.dumps(compact_input, separators=(",", ":"), ensure_ascii=False)}]}], "text": {"format": {"type": "json_schema", "name": "movement_coach_observations", "strict": True, "schema": OBSERVATION_SCHEMA}}, "max_output_tokens": 1000}
    started = time.perf_counter()
    try:
        response = _request(payload, os.environ["OPENAI_API_KEY"])
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"OpenAI reasoning unavailable: {type(exc).__name__}") from exc
    data = json.loads(_output_text(response))
    observations = data.get("observations")
    if not isinstance(observations, list) or len(observations) > 5 or not isinstance(data.get("summary"), str):
        raise ValueError("Respuesta de razonamiento inválida")
    if not compact_input["reasoning_eligibility"]["can_generate_observations"]:
        observations = []
        data["summary"] = "No hay evidencia suficiente en la captura o el conteo para generar observaciones automáticas."
    repetition_numbers = {item["number"] for item in compact_input["repetitions"] if item["number"] is not None}
    duration = (result.get("video") or {}).get("duration_s")
    accepted_observations = []
    for observation in observations:
        if not isinstance(observation, dict) or observation.get("severity") not in {"info", "review", "priority"} or observation.get("confidence") not in {"low", "medium", "high"}:
            raise ValueError("Observación IA inválida")
        if observation.get("repetition") is not None and observation["repetition"] not in repetition_numbers:
            raise ValueError("La observación IA refiere una repetición inexistente")
        timestamp = observation.get("timestamp")
        if timestamp is not None and (not isinstance(timestamp, (int, float)) or timestamp < 0 or (isinstance(duration, (int, float)) and timestamp > duration)):
            raise ValueError("El timestamp de la observación IA es inválido")
        if not _has_grounded_numeric_evidence(observation.get("evidence"), compact_input):
            evidence = _fallback_evidence(observation, compact_input)
            if evidence is None:
                continue
            observation["evidence"] = evidence
        accepted_observations.append(observation)
    return ReasoningResult(observations=_unique_observations(accepted_observations), summary=data["summary"], model=model, usage=response.get("usage") or {}, latency_ms=round((time.perf_counter() - started) * 1000))
