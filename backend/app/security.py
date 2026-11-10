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


def sign_state(clerk_id: str, secret: str, ttl_seconds: int = 600) -> str:
    payload = {
        "clerkId": clerk_id,
        "exp": int(time.time()) + ttl_seconds,
        "nonce": secrets.token_hex(8),
    }
    raw = base64.urlsafe_b64encode(json.dumps(payload, separators=(",", ":")).encode()).decode().rstrip("=")
    signature = hmac.new(secret.encode(), raw.encode(), hashlib.sha256).hexdigest()
    return f"{raw}.{signature}"


def verify_state(state: str, secret: str) -> str:
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
    if not isinstance(clerk_id, str) or not clerk_id:
        raise ValueError("invalid oauth state")
    return clerk_id
