from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4
from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, String, Text, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from ..database import Base


class AthleteIdentity(Base):
    __tablename__ = 'athlete_identity'
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    athlete_id: Mapped[UUID] = mapped_column(ForeignKey('athletes.user_id'), index=True)
    phone_encrypted: Mapped[str] = mapped_column(Text)
    phone_hash: Mapped[str] = mapped_column(String(64))
    key_version: Mapped[str] = mapped_column(String(32))
    verified_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    __table_args__ = (
        Index('uq_identity_active_phone', 'phone_hash', unique=True, postgresql_where=text('revoked_at IS NULL')),
        Index('uq_identity_active_athlete', 'athlete_id', unique=True, postgresql_where=text('revoked_at IS NULL')),
    )


class LinkChallenge(Base):
    __tablename__ = 'whatsapp_link_challenges'
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    athlete_id: Mapped[UUID] = mapped_column(ForeignKey('athletes.user_id'), index=True)
    code_hash: Mapped[str] = mapped_column(String(64), unique=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, server_default='0')
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    consumed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class WhatsAppPeer(Base):
    __tablename__ = 'whatsapp_peers'
    phone_hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    attempts: Mapped[int] = mapped_column(Integer, default=0, server_default='0')
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class WhatsAppInbox(Base):
    __tablename__ = 'whatsapp_inbox'
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    provider: Mapped[str] = mapped_column(String(16))
    provider_message_id: Mapped[str] = mapped_column(String(240))
    message_type: Mapped[str] = mapped_column(String(24))
    event: Mapped[str] = mapped_column(String(24), default='received')
    peer_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    athlete_id: Mapped[UUID | None] = mapped_column(ForeignKey('athletes.user_id'))
    payload_encrypted: Mapped[str | None] = mapped_column(Text)
    key_version: Mapped[str] = mapped_column(String(32))
    state: Mapped[str] = mapped_column(String(24), default='PENDING', server_default='PENDING', index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, server_default='0')
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    happened_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(64))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint('provider', 'provider_message_id', name='uq_whatsapp_inbox_message'),)


class WhatsAppOutbox(Base):
    __tablename__ = 'whatsapp_outbox'
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    athlete_id: Mapped[UUID | None] = mapped_column(ForeignKey('athletes.user_id'), index=True)
    dedupe_key: Mapped[str] = mapped_column(String(160), unique=True)
    action: Mapped[str] = mapped_column(String(32))
    payload_encrypted: Mapped[str | None] = mapped_column(Text)
    key_version: Mapped[str] = mapped_column(String(32))
    provider_message_id: Mapped[str | None] = mapped_column(String(240), index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0, server_default='0')
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    state: Mapped[str] = mapped_column(String(24), default='PENDING', server_default='PENDING', index=True)
    lease_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_code: Mapped[str | None] = mapped_column(String(64))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ConversationState(Base):
    __tablename__ = 'conversation_state'
    athlete_id: Mapped[UUID] = mapped_column(ForeignKey('athletes.user_id'), primary_key=True)
    channel: Mapped[str] = mapped_column(String(16), primary_key=True, default='whatsapp')
    state: Mapped[str] = mapped_column(String(32), default='IDLE')
    pending_action: Mapped[str | None] = mapped_column(String(100))
    payload_minimized: Mapped[str | None] = mapped_column(Text)
    key_version: Mapped[str] = mapped_column(String(32))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    version: Mapped[int] = mapped_column(Integer, default=0, server_default='0')


class WhatsAppUsage(Base):
    __tablename__ = 'whatsapp_usage'
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    athlete_id: Mapped[UUID | None] = mapped_column(ForeignKey('athletes.user_id'), index=True)
    event_key: Mapped[str] = mapped_column(String(200), unique=True)
    category: Mapped[str] = mapped_column(String(32))
    units: Mapped[int] = mapped_column(Integer, default=1)
    cost: Mapped[Decimal | None] = mapped_column(Numeric(18, 8))
    currency: Mapped[str] = mapped_column(String(3), default='USD')
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
