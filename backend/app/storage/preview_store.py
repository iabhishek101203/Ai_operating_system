from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
import json
from secrets import token_urlsafe


class PreviewAuthorizationError(ValueError):
    """Raised when a confirmation does not correspond to a fresh preview."""


@dataclass(frozen=True)
class PreviewAuthorization:
    intent_digest: str
    expires_at: datetime


class PreviewStore:
    """Short-lived, one-time confirmation tokens bound to an exact intent."""

    def __init__(self, ttl_seconds: int) -> None:
        self._ttl_seconds = ttl_seconds
        self._items: dict[str, PreviewAuthorization] = {}

    def issue(self, intent_payload: dict[str, object]) -> str:
        self._discard_expired()
        token = token_urlsafe(32)
        self._items[token] = PreviewAuthorization(
            intent_digest=self._digest(intent_payload),
            expires_at=datetime.now(UTC) + timedelta(seconds=self._ttl_seconds),
        )
        return token

    def consume(self, token: str, intent_payload: dict[str, object]) -> None:
        self._discard_expired()
        authorization = self._items.pop(token, None)
        if authorization is None:
            raise PreviewAuthorizationError("Confirmation token is invalid, expired, or already used.")
        if authorization.intent_digest != self._digest(intent_payload):
            raise PreviewAuthorizationError("Confirmation token does not match this previewed operation.")

    @staticmethod
    def _digest(payload: dict[str, object]) -> str:
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
        return sha256(canonical.encode("utf-8")).hexdigest()

    def _discard_expired(self) -> None:
        now = datetime.now(UTC)
        self._items = {token: item for token, item in self._items.items() if item.expires_at > now}
