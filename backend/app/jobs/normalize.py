import re

# Keep this list identical to frontend/utils/normalize.ts.
_DROP = {
    "inc",
    "llc",
    "ltd",
    "corp",
    "co",
    "company",
    "incorporated",
    "limited",
    "plc",
}

_ROLE_NOISE = re.compile(r"\b(role|position|opening|opportunity)\b")


def normalize_key(value: str | None) -> str:
    text = (value or "").lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    tokens = [token for token in text.split() if token and token not in _DROP]
    return " ".join(tokens)


def normalize_role(value: str | None) -> str:
    text = _ROLE_NOISE.sub(" ", normalize_key(value))
    return " ".join(text.split())
