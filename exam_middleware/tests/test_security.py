"""
Tests for security utilities.

Covers:
  - JWT creation and decoding
  - Password hashing and verification
  - TokenEncryption (AES-256 Fernet encrypt/decrypt)
  - File hash computation
  - Transaction ID generation (idempotency)
  - Filename sanitization
"""

import pytest
from app.core.security import (
    create_access_token,
    decode_access_token,
    verify_password,
    get_password_hash,
    TokenEncryption,
    compute_file_hash,
    generate_transaction_id,
    sanitize_filename,
)


# ======================================================================
# JWT Tokens
# ======================================================================

class TestJWT:
    def test_create_and_decode_roundtrip(self):
        payload = {"sub": "admin", "type": "staff", "user_id": 1, "username": "admin"}
        token = create_access_token(data=payload)
        decoded = decode_access_token(token)

        assert decoded is not None
        assert decoded["sub"] == "admin"
        assert decoded["user_id"] == 1
        assert "exp" in decoded
        assert "jti" in decoded

    def test_invalid_token_returns_none(self):
        result = decode_access_token("not.a.valid.jwt.token")
        assert result is None

    def test_empty_token_returns_none(self):
        result = decode_access_token("")
        assert result is None


# ======================================================================
# Password Hashing
# ======================================================================

class TestPasswordHashing:
    def test_hash_and_verify(self):
        plain = "admin123"
        hashed = get_password_hash(plain)

        assert hashed != plain
        assert verify_password(plain, hashed) is True

    def test_wrong_password_fails(self):
        hashed = get_password_hash("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_hash_is_unique_per_call(self):
        """bcrypt generates a random salt each time."""
        h1 = get_password_hash("same_password")
        h2 = get_password_hash("same_password")
        assert h1 != h2  # Different salts

    def test_invalid_hash_returns_false(self):
        assert verify_password("anything", "not_a_valid_hash") is False


# ======================================================================
# Token Encryption (AES-256 Fernet)
# ======================================================================

class TestTokenEncryption:
    def test_encrypt_decrypt_roundtrip(self):
        enc = TokenEncryption(key="test-secret-key")
        original = "c53569d516cd601cb78849cd64f59eaa"

        encrypted = enc.encrypt(original)
        assert encrypted != original  # It's actually encrypted

        decrypted = enc.decrypt(encrypted)
        assert decrypted == original

    def test_different_keys_cannot_decrypt(self):
        enc1 = TokenEncryption(key="key-one")
        enc2 = TokenEncryption(key="key-two")

        encrypted = enc1.encrypt("secret_token")
        with pytest.raises(Exception):
            enc2.decrypt(encrypted)

    def test_encrypted_output_is_string(self):
        enc = TokenEncryption(key="test")
        result = enc.encrypt("hello")
        assert isinstance(result, str)


# ======================================================================
# File Hash
# ======================================================================

class TestFileHash:
    def test_deterministic(self):
        content = b"hello world pdf content"
        h1 = compute_file_hash(content)
        h2 = compute_file_hash(content)
        assert h1 == h2
        assert len(h1) == 64  # SHA-256 hex

    def test_different_content_different_hash(self):
        assert compute_file_hash(b"file_a") != compute_file_hash(b"file_b")

    def test_empty_content(self):
        result = compute_file_hash(b"")
        assert len(result) == 64


# ======================================================================
# Transaction ID (Idempotency)
# ======================================================================

class TestTransactionId:
    def test_deterministic(self):
        id1 = generate_transaction_id("212222240047", "19AI405")
        id2 = generate_transaction_id("212222240047", "19AI405")
        assert id1 == id2
        assert len(id1) == 32

    def test_different_inputs_different_ids(self):
        id1 = generate_transaction_id("212222240047", "19AI405")
        id2 = generate_transaction_id("212222240047", "ML")
        assert id1 != id2


# ======================================================================
# Filename Sanitization
# ======================================================================

class TestSanitizeFilename:
    def test_removes_path_traversal(self):
        result = sanitize_filename("../../etc/passwd")
        assert ".." not in result
        assert "/" not in result

    def test_preserves_normal_filename(self):
        result = sanitize_filename("212222240047_19AI405.pdf")
        assert "212222240047" in result
        assert ".pdf" in result

    def test_removes_dangerous_characters(self):
        result = sanitize_filename("file<script>alert('x')</script>.pdf")
        assert "<" not in result
        assert ">" not in result

    def test_empty_input_gets_fallback(self):
        result = sanitize_filename("")
        assert len(result) > 0
        assert result.startswith("file_")
