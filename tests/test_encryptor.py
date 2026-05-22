"""Tests for envchain.encryptor."""

import pytest

from envchain.encryptor import (
    ENCRYPTED_PREFIX,
    EncryptionError,
    decrypt_value,
    decrypt_vars,
    encrypt_value,
    encrypt_vars,
    is_encrypted,
)

PASS = "s3cr3t"


# ---------------------------------------------------------------------------
# encrypt_value / decrypt_value round-trip
# ---------------------------------------------------------------------------

def test_encrypt_returns_prefixed_string():
    token = encrypt_value("hello", PASS)
    assert token.startswith(ENCRYPTED_PREFIX)


def test_encrypt_decrypt_roundtrip():
    original = "my-secret-value"
    token = encrypt_value(original, PASS)
    assert decrypt_value(token, PASS) == original


def test_encrypt_same_value_differs_each_call():
    t1 = encrypt_value("value", PASS)
    t2 = encrypt_value("value", PASS)
    assert t1 != t2, "Identical plaintexts should produce different ciphertext due to random salt"


def test_decrypt_wrong_passphrase_returns_garbage():
    token = encrypt_value("secret", PASS)
    result = decrypt_value(token, "wrongpass")
    assert result != "secret"


def test_decrypt_missing_prefix_raises():
    with pytest.raises(EncryptionError, match="missing prefix"):
        decrypt_value("plaintext", PASS)


def test_decrypt_invalid_base64_raises():
    with pytest.raises(EncryptionError, match="Invalid base64"):
        decrypt_value(f"{ENCRYPTED_PREFIX}!!!not-base64!!!", PASS)


def test_decrypt_short_payload_raises():
    import base64
    short = base64.b64encode(b"tooshort").decode()
    with pytest.raises(EncryptionError, match="too short"):
        decrypt_value(f"{ENCRYPTED_PREFIX}{short}", PASS)


# ---------------------------------------------------------------------------
# is_encrypted
# ---------------------------------------------------------------------------

def test_is_encrypted_true_for_token():
    token = encrypt_value("x", PASS)
    assert is_encrypted(token) is True


def test_is_encrypted_false_for_plain():
    assert is_encrypted("plain-value") is False


# ---------------------------------------------------------------------------
# encrypt_vars / decrypt_vars
# ---------------------------------------------------------------------------

def test_encrypt_vars_all_keys_by_default():
    vars_ = {"A": "1", "B": "2"}
    result = encrypt_vars(vars_, PASS)
    assert is_encrypted(result["A"])
    assert is_encrypted(result["B"])


def test_encrypt_vars_selective_keys():
    vars_ = {"A": "1", "B": "2"}
    result = encrypt_vars(vars_, PASS, keys=["A"])
    assert is_encrypted(result["A"])
    assert not is_encrypted(result["B"])


def test_encrypt_vars_skips_already_encrypted():
    vars_ = {"A": "1"}
    once = encrypt_vars(vars_, PASS)
    twice = encrypt_vars(once, PASS)
    assert once["A"] == twice["A"], "Already-encrypted values should not be double-encrypted"


def test_decrypt_vars_roundtrip():
    vars_ = {"X": "alpha", "Y": "beta"}
    encrypted = encrypt_vars(vars_, PASS)
    decrypted = decrypt_vars(encrypted, PASS)
    assert decrypted == vars_


def test_decrypt_vars_leaves_plain_values_untouched():
    vars_ = {"PLAIN": "value", "SECRET": encrypt_value("hidden", PASS)}
    result = decrypt_vars(vars_, PASS)
    assert result["PLAIN"] == "value"
    assert result["SECRET"] == "hidden"
