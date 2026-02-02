import hashlib
import os
import hmac

# You can store this in .env
SALT = os.getenv("PASSWORD_SALT", "my_static_salt")


def hash_password(password: str) -> str:
    """
    Hash a password using SHA-256 + salt
    """
    if not isinstance(password, str):
        raise TypeError("Password must be a string")

    salted_password = f"{password}{SALT}".encode("utf-8")
    return hashlib.sha256(salted_password).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash
    """
    expected_hash = hash_password(plain_password)
    return hmac.compare_digest(expected_hash, hashed_password)
