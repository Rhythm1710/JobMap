from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings

_PRISMA_PARAMS = {"schema", "pgbouncer", "connection_limit", "pool_timeout", "connect_timeout"}


class Base(DeclarativeBase):
    pass


def normalize_database_url(url: str) -> str:
    """Accept Prisma-style URLs and return one psycopg2 can open."""
    value = (url or "").strip()
    if not value:
        return ""
    if value.startswith("postgres://"):
        value = "postgresql://" + value[len("postgres://") :]
    parts = urlsplit(value)
    query = [
        (key, item)
        for key, item in parse_qsl(parts.query, keep_blank_values=True)
        if key not in _PRISMA_PARAMS
    ]
    return urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment))


_engine = None
SessionLocal = None


def get_engine():
    global _engine, SessionLocal
    if _engine is not None:
        return _engine
    url = normalize_database_url(get_settings().database_url)
    if not url:
        return None
    _engine = create_engine(url, pool_pre_ping=True)
    SessionLocal = sessionmaker(bind=_engine, autoflush=False, autocommit=False)
    return _engine


def create_session():
    if get_engine() is None:
        return None
    return SessionLocal()


def reset_engine() -> None:
    """Drop the cached engine. Used when settings change (tests)."""
    global _engine, SessionLocal
    if _engine is not None:
        _engine.dispose()
    _engine = None
    SessionLocal = None
