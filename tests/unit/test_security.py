import pytest
from datetime import timedelta
from jose import JWTError
from jose.exceptions import ExpiredSignatureError
from agent_aichain.core.security import Security


def test_password_hashing():
    """Test password hashing and verification"""
    password = "secure_password_123"
    hashed = Security.get_password_hash(password)
    assert hashed != password
    assert Security.verify_password(password, hashed) is True
    assert Security.verify_password("wrong_password", hashed) is False


def test_create_access_token():
    """Test JWT token creation"""
    data = {"sub": "user@example.com", "tenant_id": 1}
    token = Security.create_access_token(data)
    assert isinstance(token, str)
    assert len(token) > 0


def test_decode_token():
    """Test JWT token decoding"""
    data = {"sub": "user@example.com", "tenant_id": 1}
    token = Security.create_access_token(data)
    decoded = Security.decode_token(token)
    assert decoded is not None
    assert decoded["sub"] == "user@example.com"
    assert decoded["tenant_id"] == 1


def test_decode_invalid_token():
    """Test decoding invalid token raises JWTError"""
    with pytest.raises(JWTError):
        Security.decode_token("invalid-token")


def test_decode_expired_token():
    """Test decoding expired token raises ExpiredSignatureError"""
    # Create an already expired token
    data = {"sub": "user@example.com", "tenant_id": 1}
    token = Security.create_access_token(data, expires_delta=timedelta(seconds=-1))
    with pytest.raises(ExpiredSignatureError):
        Security.decode_token(token)