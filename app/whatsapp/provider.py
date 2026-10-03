from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Protocol
from .security import ChannelError


@dataclass(frozen=True)
class InboundWhatsAppMessage:
    provider_message_id: str
    phone: str | None
    message_type: str
    timestamp: str
    text: str = ''
    media_reference: str | None = None
    media_mime: str | None = None
    action_id: str | None = None
    event: str = 'received'

    def minimized(self):
        return asdict(self)

    @property
    def happened_at(self):
        return datetime.fromisoformat(self.timestamp).astimezone(timezone.utc)


@dataclass(frozen=True)
class DownloadedMedia:
    data: bytes
    mime: str


class ProviderError(ChannelError):
    def __init__(self, code, *, safe_retry=False, uncertain=False):
        super().__init__(code)
        self.safe_retry = safe_retry
        self.uncertain = uncertain


class WhatsAppProvider(Protocol):
    def verify_webhook(self, raw: bytes, signature: str | None) -> bool: ...
    def normalize(self, raw: bytes, event: str) -> list[InboundWhatsAppMessage]: ...
    def send(self, phone: str, text: str, actions: list[dict] | None = None) -> str: ...
    def download_media(self, reference: str, max_bytes: int) -> DownloadedMedia: ...
