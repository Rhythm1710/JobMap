from cryptography.fernet import Fernet, InvalidToken


def _fernet(key: str) -> Fernet:
    if not key:
        raise RuntimeError("TOKEN_ENCRYPTION_KEY is not configured")
    try:
        return Fernet(key.encode() if isinstance(key, str) else key)
    except (ValueError, TypeError) as error:
        raise RuntimeError("TOKEN_ENCRYPTION_KEY must be a Fernet key") from error


def encrypt_secret(value: str, key: str) -> str:
    return _fernet(key).encrypt(value.encode()).decode()


def decrypt_secret(value: str, key: str) -> str:
    try:
        return _fernet(key).decrypt(value.encode()).decode()
    except InvalidToken as error:
        raise RuntimeError("could not decrypt stored token") from error
