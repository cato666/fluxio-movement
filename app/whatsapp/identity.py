from datetime import datetime, timedelta, timezone
import hmac
import secrets
from uuid import UUID, uuid4
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from ..models import Athlete
from .models import AthleteIdentity, ConversationState, LinkChallenge, WhatsAppOutbox, WhatsAppPeer
from .security import ChannelError, code_hash, normalize_phone


def now():
    return datetime.now(timezone.utc)


class IdentityResolver:
    def __init__(self, session, vault):
        self.session = session
        self.vault = vault

    def resolve(self, phone):
        if phone is None:
            return None
        return self.session.scalar(select(AthleteIdentity.athlete_id).where(
            AthleteIdentity.phone_hash == self.vault.phone_hash(phone),
            AthleteIdentity.revoked_at.is_(None)))

    def issue(self, athlete_id):
        self.session.scalar(select(Athlete).where(Athlete.user_id == athlete_id).with_for_update())
        count = self.session.scalar(select(func.count()).select_from(LinkChallenge).where(
            LinkChallenge.athlete_id == athlete_id, LinkChallenge.created_at > now() - timedelta(hours=1)))
        if count >= 3:
            raise ChannelError('link_rate_limited')
        identifier = uuid4()
        code = f'{identifier.hex}.{secrets.token_urlsafe(24)}'
        expires = now() + timedelta(minutes=10)
        self.session.add(LinkChallenge(id=identifier, athlete_id=athlete_id,
                                       code_hash=code_hash(code), expires_at=expires))
        return {'code': 'VINCULAR ' + code, 'expires_at': expires}

    def verify(self, code, phone):
        peer_key = self.vault.phone_hash(phone)
        self.session.execute(insert(WhatsAppPeer).values(phone_hash=peer_key, window_start=now(), attempts=0)
                             .on_conflict_do_nothing())
        peer = self.session.scalar(select(WhatsAppPeer).where(WhatsAppPeer.phone_hash == peer_key).with_for_update())
        if peer.window_start < now() - timedelta(hours=1):
            peer.window_start, peer.attempts = now(), 0
        peer.attempts += 1
        if peer.attempts > 20:
            return None
        try:
            identifier = UUID(code.split('.')[0])
        except (ValueError, AttributeError):
            return None
        challenge = self.session.scalar(select(LinkChallenge).where(LinkChallenge.id == identifier).with_for_update())
        if challenge is None or challenge.consumed_at or challenge.expires_at <= now() or challenge.attempts >= 5:
            return None
        challenge.attempts += 1
        if not hmac.compare_digest(challenge.code_hash, code_hash(code)):
            return None
        self.session.scalar(select(Athlete).where(Athlete.user_id == challenge.athlete_id).with_for_update())
        active = self.session.scalars(select(AthleteIdentity).where(AthleteIdentity.revoked_at.is_(None),
            (AthleteIdentity.phone_hash == peer_key) | (AthleteIdentity.athlete_id == challenge.athlete_id))).all()
        if active:
            if len(active) != 1 or active[0].athlete_id != challenge.athlete_id or active[0].phone_hash != peer_key:
                return None
        else:
            self.session.add(AthleteIdentity(athlete_id=challenge.athlete_id,
                phone_encrypted=self.vault.encrypt(normalize_phone(phone)), phone_hash=peer_key,
                key_version=self.vault.version, verified_at=now()))
        challenge.consumed_at = now()
        self.session.flush()
        return challenge.athlete_id

    def revoke(self, athlete_id):
        self.session.scalar(select(Athlete).where(Athlete.user_id == athlete_id).with_for_update())
        for identity in self.session.scalars(select(AthleteIdentity).where(
            AthleteIdentity.athlete_id == athlete_id, AthleteIdentity.revoked_at.is_(None)).with_for_update()):
            identity.revoked_at = now()
        for challenge in self.session.scalars(select(LinkChallenge).where(
            LinkChallenge.athlete_id == athlete_id, LinkChallenge.consumed_at.is_(None))):
            challenge.consumed_at = now()
        state = self.session.get(ConversationState, (athlete_id, 'whatsapp'))
        if state:
            state.state, state.pending_action, state.payload_minimized = 'IDLE', None, None
            state.version += 1
        for item in self.session.scalars(select(WhatsAppOutbox).where(WhatsAppOutbox.athlete_id == athlete_id,
            WhatsAppOutbox.state.in_(('PENDING', 'RETRY'))).with_for_update()):
            item.state, item.payload_encrypted = 'CANCELLED', None
