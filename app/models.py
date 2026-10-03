"""F1 persistence schema; review workflows are implemented in later phases."""
from datetime import date, datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint, Date, DateTime, Float, ForeignKey, ForeignKeyConstraint,
    Index, Integer, String, Text, UniqueConstraint, func, text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    demo_key: Mapped[str | None] = mapped_column(String(40), unique=True)
    name: Mapped[str] = mapped_column(String(160))
    role: Mapped[str] = mapped_column(String(16))
    password_hash: Mapped[str | None] = mapped_column(Text)
    is_internal: Mapped[bool] = mapped_column(server_default=text('false'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint("role IN ('ATHLETE', 'COACH', 'SYSTEM_ADMIN')", name="ck_users_role"),
        UniqueConstraint("id", "role", name="uq_users_id_role"),
    )


class Athlete(Base):
    __tablename__ = "athletes"
    user_id: Mapped[UUID] = mapped_column(primary_key=True)
    role: Mapped[str] = mapped_column(String(16), server_default="ATHLETE")
    __table_args__ = (
        ForeignKeyConstraint(["user_id", "role"], ["users.id", "users.role"], name="fk_athletes_user_role"),
        CheckConstraint("role = 'ATHLETE'", name="ck_athletes_role"),
    )


class TrainingSession(Base):
    __tablename__ = "training_sessions"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    athlete_id: Mapped[UUID] = mapped_column(ForeignKey("athletes.user_id"), index=True)
    trained_on: Mapped[date] = mapped_column(Date)
    title: Mapped[str] = mapped_column(String(160))
    source_text: Mapped[str] = mapped_column(Text)
    workout: Mapped[str] = mapped_column(Text)
    result_text: Mapped[str | None] = mapped_column(Text)
    adaptations: Mapped[str | None] = mapped_column(Text)
    rpe: Mapped[int | None] = mapped_column(Integer)
    video_links: Mapped[list] = mapped_column(JSONB, default=list)
    blocks: Mapped[list] = mapped_column(JSONB, default=list)
    source_image_id: Mapped[UUID | None] = mapped_column(ForeignKey('training_images.id'))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (CheckConstraint("rpe IS NULL OR rpe BETWEEN 1 AND 10", name="ck_training_sessions_rpe"),)


class TrainingImage(Base):
    __tablename__ = 'training_images'
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    athlete_id: Mapped[UUID] = mapped_column(ForeignKey('athletes.user_id'), index=True)
    path: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Coach(Base):
    __tablename__ = "coaches"
    user_id: Mapped[UUID] = mapped_column(primary_key=True)
    role: Mapped[str] = mapped_column(String(16), server_default="COACH")
    specialty: Mapped[str] = mapped_column(String(80))
    bio: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (
        ForeignKeyConstraint(["user_id", "role"], ["users.id", "users.role"], name="fk_coaches_user_role"),
        CheckConstraint("role = 'COACH'", name="ck_coaches_role"),
    )


class Analysis(Base):
    __tablename__ = "analyses"
    id: Mapped[str] = mapped_column(String(32), primary_key=True)
    athlete_id: Mapped[UUID] = mapped_column(ForeignKey("athletes.user_id"), index=True)
    status: Mapped[str] = mapped_column(String(16), server_default="PROCESSING")
    exercise: Mapped[str | None] = mapped_column(String(100))
    load_kg: Mapped[float | None] = mapped_column(Float)
    objective: Mapped[str | None] = mapped_column(Text)
    original_filename: Mapped[str] = mapped_column(Text)
    video_path: Mapped[str] = mapped_column(Text)
    view: Mapped[str] = mapped_column(String(16), server_default='side')
    source_analysis_id: Mapped[str | None] = mapped_column(ForeignKey("analyses.id"), index=True)
    annotated_video_path: Mapped[str | None] = mapped_column(Text)
    analysis_json_path: Mapped[str | None] = mapped_column(Text)
    thumbnail_path: Mapped[str | None] = mapped_column(Text)
    progress: Mapped[int] = mapped_column(Integer, server_default='0')
    stage: Mapped[str | None] = mapped_column(String(32))
    result: Mapped[dict | None] = mapped_column(JSONB)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("id", "athlete_id", name="uq_analyses_id_athlete"),
        CheckConstraint("status IN ('PENDING', 'PROCESSING', 'COMPLETED', 'FAILED')", name="ck_analyses_status"),
        CheckConstraint("load_kg >= 0 AND load_kg < 'Infinity'::float8", name="ck_analyses_load_kg"),
        CheckConstraint("status != 'COMPLETED' OR (result IS NOT NULL AND annotated_video_path IS NOT NULL AND completed_at IS NOT NULL)", name="ck_analyses_completed"),
        CheckConstraint("status != 'FAILED' OR error IS NOT NULL", name="ck_analyses_failed"),
    )


class Repetition(Base):
    __tablename__ = "repetitions"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id"), index=True)
    number: Mapped[int] = mapped_column(Integer)
    start_s: Mapped[float] = mapped_column(Float)
    bottom_s: Mapped[float] = mapped_column(Float)
    end_s: Mapped[float] = mapped_column(Float)
    metrics: Mapped[dict] = mapped_column(JSONB)
    source: Mapped[str] = mapped_column(String(16), server_default="DETECTED")
    correction_status: Mapped[str] = mapped_column(String(16), server_default="ACTIVE")
    correction_note: Mapped[str | None] = mapped_column(Text)
    __table_args__ = (
        UniqueConstraint("analysis_id", "number", name="uq_repetitions_number"),
        UniqueConstraint("id", "analysis_id", name="uq_repetitions_analysis"),
        CheckConstraint("number > 0", name="ck_repetitions_number"),
        CheckConstraint("source IN ('DETECTED', 'MANUAL')", name="ck_repetitions_source"),
        CheckConstraint("correction_status IN ('ACTIVE', 'DISCARDED')", name="ck_repetitions_correction_status"),
        CheckConstraint("start_s >= 0 AND bottom_s >= start_s AND end_s >= bottom_s AND end_s < 'Infinity'::float8", name="ck_repetitions_times"),
    )


class CoachReview(Base):
    __tablename__ = "reviews"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id"), index=True)
    athlete_id: Mapped[UUID] = mapped_column()
    coach_id: Mapped[UUID] = mapped_column(ForeignKey("coaches.user_id"), index=True)
    status: Mapped[str] = mapped_column(String(16), server_default="PENDING")
    best_repetition_id: Mapped[UUID | None] = mapped_column()
    work_repetition_id: Mapped[UUID | None] = mapped_column()
    strengths: Mapped[str | None] = mapped_column(Text)
    main_focus: Mapped[str | None] = mapped_column(Text)
    next_session: Mapped[str | None] = mapped_column(Text)
    summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        UniqueConstraint("id", "analysis_id", name="uq_reviews_analysis"),
        ForeignKeyConstraint(
            ["analysis_id", "athlete_id"], ["analyses.id", "analyses.athlete_id"],
            name="fk_reviews_analysis_athlete",
        ),
        ForeignKeyConstraint(["best_repetition_id", "analysis_id"], ["repetitions.id", "repetitions.analysis_id"], name="fk_reviews_best_rep"),
        ForeignKeyConstraint(["work_repetition_id", "analysis_id"], ["repetitions.id", "repetitions.analysis_id"], name="fk_reviews_work_rep"),
        CheckConstraint("status IN ('PENDING', 'IN_REVIEW', 'COMPLETED')", name="ck_reviews_status"),
        CheckConstraint("status != 'COMPLETED' OR (main_focus IS NOT NULL AND length(trim(main_focus)) > 0 AND next_session IS NOT NULL AND length(trim(next_session)) > 0 AND completed_at IS NOT NULL)", name="ck_reviews_completed"),
        Index(
            "uq_reviews_active_analysis_coach", "analysis_id", "coach_id", unique=True,
            postgresql_where=text("status IN ('PENDING', 'IN_REVIEW')"),
        ),
    )


# Compatibility with F1.1's provisional model name.
Review = CoachReview


class Annotation(Base):
    __tablename__ = "annotations"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    review_id: Mapped[UUID] = mapped_column(ForeignKey("reviews.id"), index=True)
    timestamp_s: Mapped[float] = mapped_column(Float)
    body: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint("timestamp_s >= 0 AND timestamp_s < 'Infinity'::float8", name="ck_annotations_timestamp"),
        CheckConstraint("length(trim(body)) > 0", name="ck_annotations_body"),
    )


class CoachAnnotation(Base):
    __tablename__ = "coach_annotations"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    review_id: Mapped[UUID] = mapped_column(ForeignKey("reviews.id"), index=True)
    coach_id: Mapped[UUID] = mapped_column(ForeignKey("coaches.user_id"), index=True)
    timestamp_s: Mapped[float] = mapped_column(Float)
    annotation_type: Mapped[str] = mapped_column(String(16))
    text: Mapped[str] = mapped_column(Text)
    repetition_number: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    __table_args__ = (
        CheckConstraint("timestamp_s >= 0 AND timestamp_s < 'Infinity'::float8", name="ck_coach_annotations_timestamp"),
        CheckConstraint("annotation_type IN ('COMMENT', 'REVIEW', 'CORRECT', 'PRIORITY')", name="ck_coach_annotations_type"),
        CheckConstraint("length(trim(text)) > 0", name="ck_coach_annotations_text"),
        CheckConstraint("repetition_number IS NULL OR repetition_number > 0", name="ck_coach_annotations_repetition"),
        Index("ix_coach_annotations_review_timestamp", "review_id", "timestamp_s"),
    )


class AIObservation(Base):
    __tablename__ = "ai_observations"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id"), index=True)
    body: Mapped[str] = mapped_column(Text)
    timestamp_s: Mapped[float | None] = mapped_column(Float)
    repetition_number: Mapped[int | None] = mapped_column(Integer)
    category: Mapped[str | None] = mapped_column(String(80))
    severity: Mapped[str | None] = mapped_column(String(16))
    title: Mapped[str | None] = mapped_column(String(240))
    description: Mapped[str | None] = mapped_column(Text)
    evidence: Mapped[str | None] = mapped_column(Text)
    confidence: Mapped[str | None] = mapped_column(String(16))
    model: Mapped[str | None] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        UniqueConstraint("id", "analysis_id", name="uq_ai_observations_analysis"),
        CheckConstraint("timestamp_s >= 0 AND timestamp_s < 'Infinity'::float8", name="ck_ai_observations_timestamp"),
        CheckConstraint("severity IS NULL OR severity IN ('info', 'review', 'priority')", name="ck_ai_observations_severity"),
        CheckConstraint("confidence IS NULL OR confidence IN ('low', 'medium', 'high')", name="ck_ai_observations_confidence"),
    )


class AIReasoningRun(Base):
    __tablename__ = "ai_reasoning_runs"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id"), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(16), server_default="PENDING")
    model: Mapped[str | None] = mapped_column(String(120))
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    reasoning_tokens: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (
        CheckConstraint("status IN ('PENDING', 'RUNNING', 'COMPLETED', 'FAILED', 'DISABLED')", name="ck_ai_reasoning_runs_status"),
    )


class AIReviewMoment(Base):
    __tablename__ = "ai_review_moments"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    analysis_id: Mapped[str] = mapped_column(ForeignKey("analyses.id"), index=True)
    observation_id: Mapped[UUID] = mapped_column(ForeignKey("ai_observations.id"), unique=True)
    repetition_number: Mapped[int | None] = mapped_column(Integer)
    timestamp_s: Mapped[float] = mapped_column(Float)
    reason: Mapped[str] = mapped_column(Text)
    confidence: Mapped[str] = mapped_column(String(16))
    priority_score: Mapped[float] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        CheckConstraint("timestamp_s >= 0 AND timestamp_s < 'Infinity'::float8", name="ck_ai_review_moments_timestamp"),
        CheckConstraint("confidence IN ('low', 'medium', 'high')", name="ck_ai_review_moments_confidence"),
    )


class AIObservationDecision(Base):
    __tablename__ = "ai_observation_decisions"
    review_id: Mapped[UUID] = mapped_column(primary_key=True)
    observation_id: Mapped[UUID] = mapped_column(primary_key=True)
    analysis_id: Mapped[str] = mapped_column(String(32))
    decision: Mapped[str] = mapped_column(String(16))
    __table_args__ = (
        ForeignKeyConstraint(["review_id", "analysis_id"], ["reviews.id", "reviews.analysis_id"], name="fk_decisions_review"),
        ForeignKeyConstraint(["observation_id", "analysis_id"], ["ai_observations.id", "ai_observations.analysis_id"], name="fk_decisions_observation"),
        CheckConstraint("decision IN ('CONFIRMED', 'DISMISSED')", name="ck_decisions_value"),
    )
