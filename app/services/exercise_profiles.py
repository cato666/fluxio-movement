from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class UnknownExerciseProfileError(ValueError):
    """Raised when a requested exercise has no parameterized detector."""


class UnsupportedViewError(ValueError):
    """Raised when a profile cannot safely interpret the camera view."""


def _normalise(value: str) -> str:
    return " ".join(value.strip().casefold().split())


@dataclass(frozen=True)
class ExerciseProfile:
    id: str
    aliases: tuple[str, ...]
    views: tuple[str, ...]
    required_landmarks: tuple[str, ...]
    primary_signal: str
    states: tuple[str, ...]
    initial_state: str
    bottom_state: str
    transitions: tuple[dict[str, Any], ...]
    thresholds: dict[str, float]
    metrics: tuple[str, ...]
    noise: dict[str, float]

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "ExerciseProfile":
        required = {
            "id", "aliases", "views", "required_landmarks", "primary_signal",
            "states", "initial_state", "bottom_state", "transitions", "thresholds",
            "metrics", "noise",
        }
        missing = required.difference(value)
        if missing:
            raise ValueError(f"Perfil de ejercicio incompleto: {', '.join(sorted(missing))}")
        if value["initial_state"] not in value["states"] or value["bottom_state"] not in value["states"]:
            raise ValueError(f"Estados inválidos en el perfil {value['id']}")
        return cls(
            id=_normalise(value["id"]),
            aliases=tuple(_normalise(alias) for alias in value["aliases"]),
            views=tuple(_normalise(view) for view in value["views"]),
            required_landmarks=tuple(value["required_landmarks"]),
            primary_signal=value["primary_signal"],
            states=tuple(value["states"]),
            initial_state=value["initial_state"],
            bottom_state=value["bottom_state"],
            transitions=tuple(value["transitions"]),
            thresholds={key: float(threshold) for key, threshold in value["thresholds"].items()},
            metrics=tuple(value["metrics"]),
            noise={key: float(noise) for key, noise in value["noise"].items()},
        )


class ExerciseProfileLoader:
    def __init__(self, directory: Path | None = None):
        self.directory = directory or Path(__file__).with_name("exercise_profiles")
        self._profiles: dict[str, ExerciseProfile] | None = None

    def profiles(self) -> dict[str, ExerciseProfile]:
        if self._profiles is None:
            loaded: dict[str, ExerciseProfile] = {}
            for source in sorted(self.directory.glob("*.json")):
                profile = ExerciseProfile.from_dict(json.loads(source.read_text(encoding="utf-8")))
                if profile.id in loaded:
                    raise ValueError(f"Perfil duplicado: {profile.id}")
                loaded[profile.id] = profile
            self._profiles = loaded
        return self._profiles

    def load(self, exercise: str, view: str = "side") -> ExerciseProfile:
        normalized_exercise = _normalise(exercise)
        normalized_view = _normalise(view)
        matches = [
            profile for profile in self.profiles().values()
            if normalized_exercise == profile.id or normalized_exercise in profile.aliases
        ]
        for profile in matches:
            if normalized_view in profile.views:
                return profile
        if matches:
            supported = ", ".join(sorted({item for profile in matches for item in profile.views}))
            raise UnsupportedViewError(
                f"La vista '{view}' no está soportada para {exercise}. Usa: {supported}."
            )
        raise UnknownExerciseProfileError(f"No hay perfil de análisis para el ejercicio '{exercise}'.")


class RepDetector:
    """State machine driven by an :class:`ExerciseProfile`, never by exercise branches."""

    def __init__(self, profile: ExerciseProfile):
        self.profile = profile
        self.state = profile.initial_state
        self._transition_streak = 0
        self._last_valid_time: float | None = None
        self._last_completed_time: float | None = None
        self._rep_start: float | None = None
        self._bottom: float | None = None
        self._rep_samples: list[dict[str, float]] = []
        self._repetitions: list[dict[str, float]] = []

    def _reset_candidate(self) -> None:
        self.state = self.profile.initial_state
        self._transition_streak = 0
        self._rep_start = None
        self._bottom = None
        self._rep_samples = []

    def _expected_transition(self) -> dict[str, Any] | None:
        return next((item for item in self.profile.transitions if item["from"] == self.state), None)

    def _matches(self, transition: dict[str, Any], sample: dict[str, float]) -> bool:
        conditions = transition.get("conditions") or [transition]
        for condition in conditions:
            value = sample.get(condition["signal"])
            threshold = self.profile.thresholds[condition["threshold"]]
            if value is None or not math.isfinite(float(value)):
                return False
            matched = float(value) <= threshold if condition["operator"] == "<=" else float(value) >= threshold
            if not matched:
                return False
        return True

    def _complete(self, time_s: float) -> None:
        if self._rep_start is None or self._bottom is None:
            return
        duration = time_s - self._rep_start
        noise = self.profile.noise
        if not noise["min_rep_duration_s"] <= duration <= noise["max_rep_duration_s"]:
            return
        if self._last_completed_time is not None and time_s - self._last_completed_time < noise["cooldown_s"]:
            return
        metrics: dict[str, float] = {}
        for metric in self.profile.metrics:
            values = [float(sample[metric]) for sample in self._rep_samples if sample.get(metric) is not None]
            if values:
                metrics[f"min_{metric}"] = round(min(values), 1)
                metrics[f"max_{metric}"] = round(max(values), 1)
        result = {
            "repetition": len(self._repetitions) + 1,
            "start_s": round(self._rep_start, 2),
            "bottom_s": round(self._bottom, 2),
            "end_s": round(time_s, 2),
            "profile": self.profile.id,
            **metrics,
        }
        self._repetitions.append(result)
        self._last_completed_time = time_s

    def consume(self, raw_sample: dict[str, Any]) -> None:
        try:
            time_s = float(raw_sample["time_s"])
        except (KeyError, TypeError, ValueError):
            return
        primary = raw_sample.get(self.profile.primary_signal)
        if primary is None or not math.isfinite(float(primary)):
            return
        if self._last_valid_time is not None and time_s - self._last_valid_time > self.profile.noise["max_gap_s"]:
            self._reset_candidate()
        self._last_valid_time = time_s
        sample = {key: raw_sample.get(key) for key in (*self.profile.metrics, self.profile.primary_signal)}
        self._rep_samples.append(sample)
        transition = self._expected_transition()
        if transition is None or not self._matches(transition, sample):
            self._transition_streak = 0
            return
        self._transition_streak += 1
        if self._transition_streak < int(self.profile.noise["min_confirm_frames"]):
            return
        self._transition_streak = 0
        previous_state = self.state
        self.state = transition["to"]
        if previous_state == self.profile.initial_state:
            self._rep_start = time_s
            self._rep_samples = [sample]
        if self.state == self.profile.bottom_state:
            self._bottom = time_s
        if transition.get("completes_rep"):
            self._complete(time_s)
            self._rep_start = None
            self._bottom = None
            self._rep_samples = []

    def detect(self, samples: list[dict[str, Any]]) -> list[dict[str, float]]:
        for sample in samples:
            self.consume(sample)
        return self._repetitions
