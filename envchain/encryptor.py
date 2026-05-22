"""Simple symmetric encryption for sensitive chain variables."""

from __future__ import annotations

import base64
import hashlib
import os
from typing import Dict

ENCRYPTED_PREFIX = "enc:"


class EncryptionError(Exception):
    """Raised when encryption or decryption fails."""


def _derive_key(passphrase: str) -> bytes:
    """Derive a 32-byte key from a passphrase using SHA-256."""
    return hashlib.sha256(passphrase.encode()).digest()


def encrypt_value(value: str, passphrase: str) -> str:
    """Encrypt *value* and return a prefixed base64 string.

    Uses XOR with a key-stream derived from the passphrase and a random salt
    so that identical values produce different ciphertext each call.
    """
    key = _derive_key(passphrase)
    salt = os.urandom(16)
    plaintext = value.encode()
    # Extend key-stream by cycling key bytes XOR'd with salt
    stream = bytearray()
    for i, b in enumerate(plaintext):
        stream.append(b ^ key[i % len(key)] ^ salt[i % len(salt)])
    payload = salt + bytes(stream)
    encoded = base64.b64encode(payload).decode()
    return f"{ENCRYPTED_PREFIX}{encoded}"


def decrypt_value(token: str, passphrase: str) -> str:
    """Decrypt a token produced by :func:`encrypt_value`.

    Raises :class:`EncryptionError` if the token is malformed.
    """
    if not token.startswith(ENCRYPTED_PREFIX):
        raise EncryptionError(f"Value is not encrypted (missing prefix '{ENCRYPTED_PREFIX}')")
    try:
        payload = base64.b64decode(token[len(ENCRYPTED_PREFIX):])
    except Exception as exc:
        raise EncryptionError(f"Invalid base64 payload: {exc}") from exc
    if len(payload) < 16:
        raise EncryptionError("Payload too short to contain salt")
    salt, ciphertext = payload[:16], payload[16:]
    key = _derive_key(passphrase)
    plaintext = bytearray()
    for i, b in enumerate(ciphertext):
        plaintext.append(b ^ key[i % len(key)] ^ salt[i % len(salt)])
    return plaintext.decode()


def is_encrypted(value: str) -> bool:
    """Return *True* if *value* looks like an encrypted token."""
    return value.startswith(ENCRYPTED_PREFIX)


def encrypt_vars(vars_: Dict[str, str], passphrase: str, keys: list[str] | None = None) -> Dict[str, str]:
    """Return a copy of *vars_* with selected *keys* encrypted.

    If *keys* is *None* all values are encrypted.
    """
    result = dict(vars_)
    targets = keys if keys is not None else list(vars_)
    for k in targets:
        if k in result and not is_encrypted(result[k]):
            result[k] = encrypt_value(result[k], passphrase)
    return result


def decrypt_vars(vars_: Dict[str, str], passphrase: str) -> Dict[str, str]:
    """Return a copy of *vars_* with all encrypted values decrypted."""
    result = {}
    for k, v in vars_.items():
        result[k] = decrypt_value(v, passphrase) if is_encrypted(v) else v
    return result
