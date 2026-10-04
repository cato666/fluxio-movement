"""Validated reference metadata; detector configuration remains in exercise_profiles."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Literal
from urllib.parse import parse_qs, urlparse

from pydantic import BaseModel, Field, model_validator

DATA = Path(__file__).with_name('exercise_library')


class ReferenceSegment(BaseModel):
    type: str
    start_sec: float = Field(ge=0, allow_inf_nan=False)
    end_sec: float = Field(gt=0, allow_inf_nan=False)

    @model_validator(mode='after')
    def ordered(self):
        if self.end_sec <= self.start_sec:
            raise ValueError('Segment end must follow start')
        return self


class ReferenceVideo(BaseModel):
    provider: Literal['youtube'] = 'youtube'
    organization: str
    source_type: Literal['official', 'community']
    video_id: str = Field(pattern=r'^[A-Za-z0-9_-]{11}$')
    url: str
    segments: list[ReferenceSegment] = Field(default_factory=list)

    @model_validator(mode='after')
    def valid_url(self):
        parsed = urlparse(self.url)
        if (parsed.scheme != 'https' or parsed.netloc not in ('www.youtube.com', 'youtube.com')
                or parsed.path != '/watch' or parse_qs(parsed.query).get('v') != [self.video_id]):
            raise ValueError('YouTube URL must match video_id')
        return self

    def embed_url(self, segment: int | None = None) -> str:
        result = f'https://www.youtube.com/embed/{self.video_id}'
        if segment is not None:
            item = self.segments[segment]
            result += f'?start={math.floor(item.start_sec)}&end={math.ceil(item.end_sec)}'
        return result


class TechnicalFault(BaseModel):
    id: str
    name: str
    description: str
    detectable: bool = False


class ProfileMetadata(BaseModel):
    name: str | None = None
    category: str | None = None
    priority: Literal['P1', 'P2', 'P3'] | None = None
    analysis_status: Literal['supported', 'reference_only'] | None = None
    supported_views: list[str] = Field(default_factory=list)
    reference_videos: list[ReferenceVideo] = Field(default_factory=list)
    phases: list[str] = Field(default_factory=list)
    faults: list[TechnicalFault] = Field(default_factory=list)
    coaching_cues: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class LibraryExercise(ProfileMetadata):
    id: str = Field(pattern=r'^[a-z][a-z0-9_]*$')
    name: str
    category: str
    priority: Literal['P1', 'P2', 'P3']
    analysis_status: Literal['supported', 'reference_only']
    required_landmarks: list[str]
    metrics: list[str] = Field(default_factory=list)
    detector_profiles: list[str] = Field(default_factory=list)


class ExerciseFinding(BaseModel):
    """Future findings contract; no reasoning or inference is run here."""
    exercise_id: str
    rep: int = Field(ge=1)
    fault_id: str
    severity: Literal['low', 'medium', 'high']
    start_sec: float = Field(ge=0, allow_inf_nan=False)
    end_sec: float = Field(gt=0, allow_inf_nan=False)
    confidence: float = Field(ge=0, le=1, allow_inf_nan=False)

    @model_validator(mode='after')
    def ordered(self):
        if self.end_sec <= self.start_sec:
            raise ValueError('Finding end must follow start')
        return self


class ExerciseLibrary:
    def __init__(self, directory: Path = DATA):
        from .exercise_profiles import ExerciseProfileLoader
        self.categories = json.loads((directory / 'taxonomy.json').read_text(encoding='utf-8'))
        self.exercises: dict[str, LibraryExercise] = {}
        detectors = ExerciseProfileLoader().profiles()
        for raw in json.loads((directory / 'exercises.json').read_text(encoding='utf-8')):
            exercise = LibraryExercise.model_validate(raw)
            if exercise.category not in self.categories or exercise.id in self.exercises:
                raise ValueError(f'Invalid category or duplicate exercise: {exercise.id}')
            if exercise.analysis_status == 'supported':
                if not exercise.detector_profiles:
                    raise ValueError('Supported exercise requires detector profiles')
                views = set()
                for profile_id in exercise.detector_profiles:
                    profile = detectors[profile_id]
                    views.update('lateral' if view == 'side' else view for view in profile.views)
                if not set(exercise.supported_views).issubset(views):
                    raise ValueError('Unsupported detector view')
            self.exercises[exercise.id] = exercise

    def list(self, category=None, priority=None, analysis_status=None):
        return [item for item in self.exercises.values()
                if all(value is None or getattr(item, key) == value for key, value in
                       [('category', category), ('priority', priority), ('analysis_status', analysis_status)])]

    def get(self, exercise_id: str):
        return self.exercises[exercise_id]
