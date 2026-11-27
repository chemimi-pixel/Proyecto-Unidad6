"""Verificacion y generacion de hashes scrypt para cuentas de la aplicacion."""

from __future__ import annotations

import base64
import hashlib
import hmac
import secrets


SCRYPT_N = 16_384
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_LENGTH = 64


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=SCRYPT_LENGTH,
    )
    return "$".join(
        (
            "scrypt",
            str(SCRYPT_N),
            str(SCRYPT_R),
            str(SCRYPT_P),
            base64.b64encode(salt).decode("ascii"),
            base64.b64encode(digest).decode("ascii"),
        )
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        algorithm, n_value, r_value, p_value, salt_value, digest_value = stored_hash.split("$")
        if algorithm != "scrypt":
            return False
        n, r, p = int(n_value), int(r_value), int(p_value)
        salt = base64.b64decode(salt_value, validate=True)
        expected = base64.b64decode(digest_value, validate=True)
        actual = hashlib.scrypt(
            password.encode("utf-8"), salt=salt, n=n, r=r, p=p,
            dklen=len(expected), maxmem=128 * 1024 * 1024,
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError, MemoryError):
        return False
