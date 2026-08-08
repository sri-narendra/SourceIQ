
from services.auth_service import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_verify_roundtrip():
    hashed = hash_password("s3cret!")
    assert hashed != "s3cret!"
    assert verify_password("s3cret!", hashed)
    assert not verify_password("wrong", hashed)


def test_hash_is_unique_salt():
    assert hash_password("same") != hash_password("same")


def test_token_roundtrip():
    token, expires = create_access_token("user-123")
    assert expires == 1440 * 60
    assert decode_access_token(token) == "user-123"


def test_decode_garbage_token_returns_none():
    assert decode_access_token("not.a.jwt") is None


def test_decode_tampered_token_returns_none():
    token, _ = create_access_token("user-123")
    assert decode_access_token(token[:-4] + "xxxx") is None
