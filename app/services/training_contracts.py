"""Shared training request validation, independent of transport."""
from datetime import date
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from .workout_interpretation import WorkoutBlock, WorkoutDraft


class InterpretPayload(BaseModel):
    text: str = Field(default='', max_length=12000)
    image_id: UUID | None = None


class VideoLink(BaseModel):
    analysis_id: str = Field(min_length=1, max_length=32)
    movement: str = Field(min_length=1, max_length=100)
    context: str = Field(default='', max_length=160)


class SessionPayload(BaseModel):
    trained_on: date
    title: str = Field(min_length=1, max_length=160)
    source_text: str = Field(default='', max_length=12000)
    workout: str = Field(min_length=1, max_length=12000)
    result_text: str | None = Field(default=None, max_length=4000)
    adaptations: str | None = Field(default=None, max_length=4000)
    rpe: int | None = Field(default=None, ge=1, le=10, strict=True)
    video_links: list[VideoLink] = Field(default_factory=list, max_length=30)
    blocks: list[WorkoutBlock] = Field(default_factory=list, max_length=12)
    source_image_id: UUID | None = None

    @field_validator('title', 'workout')
    @classmethod
    def nonblank(cls, value):
        if not value.strip():
            raise ValueError('Completa este campo')
        return value.strip()
