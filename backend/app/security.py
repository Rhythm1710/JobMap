import base64
import hashlib
import hmac
import json
import secrets
import time

from fastapi import Header, HTTPException


def require_service(authorization: str | None = Header(default=None)) -> None:
    """Shared-secret auth for calls from the Next.js server and Railway cron.

    The browser never calls this service directly. Next.js server actions attach
    the secret after Clerk has already identified the user.
    """
    from app.config import get_settings

    settings = get_settings()
    if not settings.service_secret:
        raise HTTPException(status_code=503, detail="SERVICE_SECRET is not configured")
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="missing service credentials")
    token = authorization.split(" ", 1)[1].strip()
    if not hmac.compare_digest(token, settings.service_secret):
        raise HTTPException(status_code=401, detail="invalid service credentials")


MISSING_OAUTH_COOKIE = (
    "Gmail connect could not be verified because this browser did not start it. "
    "Use Connect Gmail again in this browser."
)
MISMATCH_OAUTH_COOKIE = (
    "Gmail connect did not match this browser session. "
    "Use Connect Gmail again in this browser."
)
INVALID_OAUTH_STATE = "Gmail connect request was invalid or expired. Use Connect Gmail again."


class OauthBindingError(Exception):
    def __init__(self, reason: str, message: str):
        self.reason = reason
        super().__init__(message)


def _constant_equal(left: str, right: str) -> bool:
    return hmac.compare_digest(
        hashlib.sha256(left.encode()).digest(),
        hashlib.sha256(right.encode()).digest(),
    )


def sign_state(clerk_id: str, secret: str, browser_nonce: str, ttl_seconds: int = 600) -> str:
    """Sign a state that is only valid for the browser that holds browser_nonce."""
    if not browser_nonce or len(browser_nonce) < 16:
        raise ValueError("browser nonce is required")
    payload = {
        "clerkId": clerk_id,
        "exp": int(time.time()) + ttl_seconds,
        "nonce": browser_nonce,
        "jti": secrets.token_hex(8),
    }
    raw = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
    signature = hmac.new(secret.encode(), raw.encode(), hashlib.sha256).hexdigest()
    return f"{raw}.{signature}"


def verify_state(state: str, secret: str) -> tuple[str, str]:
    """Return (clerk_id, browser_nonce) from a signed, unexpired state."""
    if not secret or "." not in state:
        raise ValueError("invalid oauth state")
    raw, signature = state.rsplit(".", 1)
    expected = hmac.new(secret.encode(), raw.encode(), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(signature, expected):
        raise ValueError("invalid oauth state")
    padded = raw + "=" * (-len(raw) % 4)
    try:
        payload = json.loads(base64.urlsafe_b64decode(padded.encode()))
    except (json.JSONDecodeError, ValueError) as error:
        raise ValueError("invalid oauth state") from error
    if int(payload.get("exp", 0)) < int(time.time()):
        raise ValueError("oauth state expired")
    clerk_id = payload.get("clerkId")
    nonce = payload.get("nonce")
    if not isinstance(clerk_id, str) or not clerk_id:
        raise ValueError("invalid oauth state")
    if not isinstance(nonce, str) or len(nonce) < 16:
        raise ValueError("invalid oauth state")
    return clerk_id, nonce


def require_browser_binding(state: str, secret: str, browser_nonce: str | None) -> str:
    """Reject a callback whose browser cookie is missing or belongs to another attempt.

    Returns the clerk id bound into the state. Token exchange must not run unless this passes.
    """
    if browser_nonce is None or not browser_nonce.strip():
        raise OauthBindingError("missing", MISSING_OAUTH_COOKIE)
    try:
        clerk_id, expected = verify_state(state, secret)
    except ValueError as error:
        raise OauthBindingError("invalid", INVALID_OAUTH_STATE) from error
    if not _constant_equal(browser_nonce, expected):
        raise OauthBindingError("mismatch", MISMATCH_OAUTH_COOKIE)
    return clerk_id
