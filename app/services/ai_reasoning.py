"""Small, optional OpenAI reasoning layer over deterministic video analysis."""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


SYSTEM_PROMPT = """Eres un asistente técnico para coaches deportivos. Basa cada observación exclusivamente en las métricas, eventos y comparaciones recibidas. No inventes mediciones, no diagnostiques lesiones ni des recomendaciones médicas. No declares una técnica correcta o incorrecta de forma absoluta: describe patrones observables y momentos que merecen revisión humana. El coach es la autoridad final. Máximo 5 observaciones breves."""

OBSERVATION_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "required": ["observations", "summary"],
    "properties": {
        "observations": {
            "type": "array", "maxItems": 5,
            "items": {"type": "object", "additionalProperties": False,
                "required": ["repetition", "timestamp", "category", "severity", "title", "description", "confidence"],
                "properties": {
                    "repetition": {"anyOf": [{"type": "integer", "minimum": 1}, {"type": "null"}]},
                    "timestamp": {"anyOf": [{"type": "number", "minimum": 0}, {"type": "null"}]},
                    "category": {"type": "string", "maxLength": 80},
                    "severity": {"type": "string", "enum": ["info", "review", "priority"]},
                    "title": {"type": "string", "maxLength": 240},
                    "description": {"type": "string", "maxLength": 800},
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


def build_input(exercise: str, view: str, result: dict) -> dict:
    repetitions = []
    for rep in (result.get("repetitions") or [])[:20]:
        metrics = {key: rep.get(key) for key in ("min_knee_angle", "max_knee_angle", "min_hip_angle", "max_hip_angle", "min_trunk_from_vertical", "max_trunk_from_vertical", "min_elbow_angle", "lockout_elbow_angle") if rep.get(key) is not None}
        repetitions.append({"number": rep.get("repetition"), "start_s": rep.get("start_s"), "bottom_s": rep.get("bottom_s"), "end_s": rep.get("end_s"), "metrics": metrics})
    comparisons = {}
    for metric in ("min_knee_angle", "min_hip_angle", "max_trunk_from_vertical", "lockout_elbow_angle"):
        values = [rep["metrics"].get(metric) for rep in repetitions if rep["metrics"].get(metric) is not None]
        if len(values) > 1:
            comparisons[metric] = {"min": min(values), "max": max(values), "range": round(max(values) - min(values), 2)}
    return {"exercise": exercise, "view": view, "repetitions": repetitions, "metrics": result.get("summary_metrics") or {}, "events": [{"repetition": rep["number"], "bottom_s": rep["bottom_s"], "end_s": rep["end_s"]} for rep in repetitions], "comparisons": comparisons}


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
    repetition_numbers = {item["number"] for item in compact_input["repetitions"] if item["number"] is not None}
    duration = (result.get("video") or {}).get("duration_s")
    for observation in observations:
        if not isinstance(observation, dict) or observation.get("severity") not in {"info", "review", "priority"} or observation.get("confidence") not in {"low", "medium", "high"}:
            raise ValueError("Observación IA inválida")
        if observation.get("repetition") is not None and observation["repetition"] not in repetition_numbers:
            raise ValueError("La observación IA refiere una repetición inexistente")
        timestamp = observation.get("timestamp")
        if timestamp is not None and (not isinstance(timestamp, (int, float)) or timestamp < 0 or (isinstance(duration, (int, float)) and timestamp > duration)):
            raise ValueError("El timestamp de la observación IA es inválido")
    return ReasoningResult(observations=observations, summary=data["summary"], model=model, usage=response.get("usage") or {}, latency_ms=round((time.perf_counter() - started) * 1000))
