import pytest
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
import jwt
from pydantic.v1 import ValidationError

from src.web.auth.tokens import AccessToken, RefreshToken, JWTToken
from src.web.config import SECRET_KEY, ALGORITHM


class TestAccessToken:
    """Test AccessToken class functionality"""

    def test_create_access_token_defaults(self):
        """Test AccessToken creation with default values"""
        token = AccessToken(sub="user123")

        assert token.sub == "user123"
        assert token.exp > datetime.now(timezone.utc)
        assert token.iat <= datetime.now(timezone.utc)
        assert token.scope == []
        assert token.iss == ""
        assert token.aud == ""
        assert token.jti == ""

    def test_create_access_token_with_all_fields(self):
        """Test AccessToken creation with all fields populated"""
        future_time = datetime.now(timezone.utc) + timedelta(minutes=30)
        token = AccessToken(
            sub="user123",
            exp=future_time,
            iat=datetime.now(timezone.utc),
            iss="test-issuer",
            aud="test-audience",
            jti="token-123",
            scope=["read", "write"]
        )

        assert token.sub == "user123"
        assert token.exp == future_time
        assert token.iss == "test-issuer"
        assert token.aud == "test-audience"
        assert token.jti == "token-123"
        assert token.scope == ["read", "write"]

    def test_scope2str_with_scope(self):
        """Test scope to string conversion with scope present"""
        token = AccessToken(sub="user123", scope=["read", "write", "admin"])
        result = token.scope2str()

        assert result == "read write admin"

    def test_scope2str_empty_scope(self):
        """Test scope to string conversion with empty scope"""
        token = AccessToken(sub="user123", scope=[])
        result = token.scope2str()

        assert result == ""

    def test_scope2str_no_scope(self):
        """Test scope to string conversion when scope is not set"""
        token = AccessToken(sub="user123")
        result = token.scope2str()

        assert result == ""

    def test_str2list_with_spaces(self):
        """Test string to list conversion with spaces"""
        result = AccessToken.str2list("read write execute")
        assert result == ["read", "write", "execute"]

    def test_str2list_with_extra_spaces(self):
        """Test string to list conversion with extra spaces"""
        result = AccessToken.str2list("  read   write  execute  ")
        assert result == ["read", "write", "execute"]

    def test_str2list_empty_string(self):
        """Test string to list conversion with empty string"""
        result = AccessToken.str2list("")
        assert result == []

    def test_str2list_whitespace_only(self):
        """Test string to list conversion with whitespace only"""
        result = AccessToken.str2list("   ")
        assert result == []

    def test_encode_decode_roundtrip(self):
        """Test encoding and decoding preserves data"""
        original = AccessToken(
            sub="user123",
            scope=["read", "write"],
            iss="test-issuer",
            #aud="test-audience",
            jti="unique-123"
        )

        encoded = original.encode()
        decoded = AccessToken.decode(encoded)

        assert decoded.sub == original.sub
        assert decoded.scope == original.scope
        assert decoded.iss == original.iss
        #assert decoded.aud == original.aud
        assert decoded.jti == original.jti
        # exp and iat will be slightly different due to encoding/decoding process
        assert abs((decoded.exp - original.exp).total_seconds()) < 1

    def test_encode_omits_empty_fields(self):
        """Test that empty fields are omitted from JWT payload"""
        token = AccessToken(sub="user123")  # Minimal token
        encoded = token.encode()

        # Decode without verification to inspect payload
        payload = jwt.decode(encoded, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_signature": False})

        assert "sub" in payload
        assert "exp" in payload
        assert "iat" in payload
        assert "scope" not in payload  # Empty scope should be omitted
        assert "iss" not in payload  # Empty iss should be omitted
        assert "aud" not in payload  # Empty aud should be omitted

    def test_encode_includes_non_empty_fields(self):
        """Test that non-empty fields are included in JWT payload"""
        token = AccessToken(
            sub="user123",
            iss="issuer",
            aud="audience",
            scope=["read"]
        )
        encoded = token.encode()

        payload = jwt.decode(encoded, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_signature": False})

        assert payload["sub"] == "user123"
        assert payload["iss"] == "issuer"
        assert payload["aud"] == "audience"
        assert payload["scope"] == "read"  # Scope should be string in JWT

    def test_decode_invalid_token(self):
        """Test decoding invalid token raises appropriate error"""
        with pytest.raises(ValueError, match="Invalid token"):
            AccessToken.decode("invalid.token.here")

    def test_decode_tampered_token(self):
        """Test decoding tampered token raises error"""
        valid_token = AccessToken(sub="user123").encode()
        tampered_token = valid_token[:-5] + "xxxxx"  # Tamper with signature

        with pytest.raises(ValueError, match="Invalid token"):
            AccessToken.decode(tampered_token)

    def test_is_valid_with_valid_token(self):
        """Test token validation with valid token"""
        future_time = datetime.now(timezone.utc) + timedelta(minutes=60)  # Safe margin
        token = AccessToken(sub="user123", exp=future_time)
        assert token.is_valid() is True
        assert bool(token) is True

    def test_is_valid_without_subject(self):
        """Test token validation without subject"""
        token = AccessToken(sub="")
        assert token.is_valid() is False
        assert bool(token) is False




    def test_is_valid_expired_token(self):
        """Test token validation with expired token"""
        expired_time = datetime.now(timezone.utc) - timedelta(minutes=10)
        token = AccessToken(sub="user123", exp=expired_time)

        assert token.is_valid() is False
        assert bool(token) is False

    def test_is_valid_future_expiration(self):
        """Test token validation with future expiration"""
        future_time = datetime.now(timezone.utc) + timedelta(minutes=30)
        token = AccessToken(sub="user123", exp=future_time)

        assert token.is_valid() is True
        assert bool(token) is True


class TestRefreshToken:
    """Test RefreshToken class functionality"""

    def test_create_refresh_token_defaults(self):
        """Test RefreshToken creation with default values"""
        token = RefreshToken(username="john", user_id=123)

        assert token.username == "john"
        assert token.user_id == 123
        assert len(token.token_id) == 43  # token_urlsafe(32) produces 43 chars
        assert token.created_at <= datetime.now(timezone.utc)
        assert token.expires_at > datetime.now(timezone.utc)
        assert token.used is False
        assert token.use_count == 0
        assert token.client_id == ""
        assert token.last_used_at is None

    def test_create_refresh_token_custom_values(self):
        """Test RefreshToken creation with custom values"""
        created = datetime.now(timezone.utc) - timedelta(hours=1)
        expires = datetime.now(timezone.utc) + timedelta(days=7)
        last_used = datetime.now(timezone.utc) - timedelta(minutes=30)

        token = RefreshToken(
            token_id="custom-token-id",
            username="jane",
            user_id=456,
            created_at=created,
            expires_at=expires,
            used=True,
            last_used_at=last_used,
            use_count=5,
            client_id="mobile-app"
        )

        assert token.token_id == "custom-token-id"
        assert token.username == "jane"
        assert token.user_id == 456
        assert token.created_at == created
        assert token.expires_at == expires
        assert token.used is True
        assert token.last_used_at == last_used
        assert token.use_count == 5
        assert token.client_id == "mobile-app"

    def test_token_id_generation_unique(self):
        """Test that token IDs are generated uniquely"""
        token1 = RefreshToken(username="john", user_id=123)
        token2 = RefreshToken(username="john", user_id=123)

        assert token1.token_id != token2.token_id

    def test_is_valid_with_valid_token(self):
        """Test validation with valid refresh token"""
        token = RefreshToken(username="john", user_id=123)
        assert token.is_valid() is True
        assert bool(token) is True

    def test_is_valid_without_username(self):
        """Test validation without username"""
        token = RefreshToken(username="", user_id=123)
        assert token.is_valid() is False
        assert bool(token) is False

    def test_is_valid_without_user_id(self):
        """Test validation without user_id"""
        token = RefreshToken(username="john", user_id=0)
        assert token.is_valid() is False
        assert bool(token) is False

    def test_is_valid_expired_token(self):
        """Test validation with expired token"""
        expired_time = datetime.now(timezone.utc) - timedelta(hours=1)
        token = RefreshToken(
            username="john",
            user_id=123,
            expires_at=expired_time
        )
        assert token.is_valid() is False

    def test_is_valid_used_token(self):
        """Test validation with used token"""
        token = RefreshToken(username="john", user_id=123, used=True)
        assert token.is_valid() is False

   


class TestJWTToken:
    """Test JWTToken class functionality"""

    def test_create_jwt_token_pair(self):
        """Test creating JWT token pair"""
        access_token = AccessToken(sub="user123")
        refresh_token = RefreshToken(username="john", user_id=123)

        token_pair = JWTToken(
            access_token=access_token,
            refresh_token=refresh_token
        )

        assert token_pair.access_token == access_token
        assert token_pair.refresh_token == refresh_token

    def test_encode_oauth_response(self):
        """Test encoding to OAuth2 response format"""
        access_token = AccessToken(sub="user123", scope=["read", "write"])
        refresh_token = RefreshToken(username="john", user_id=123)

        token_pair = JWTToken(
            access_token=access_token,
            refresh_token=refresh_token
        )

        response = token_pair.encode()

        assert "access_token" in response
        assert "token_type" in response
        assert response["token_type"] == "bearer"
        assert "scope" in response
        assert response["scope"] == "read write"
        assert "expires_in" in response
        assert isinstance(response["expires_in"], int)
        assert response["expires_in"] > 0
        assert "refresh_token" in response
        assert response["refresh_token"] == refresh_token.token_id

    def test_encode_with_empty_scope(self):
        """Test encoding with empty scope"""
        access_token = AccessToken(sub="user123", scope=[])
        refresh_token = RefreshToken(username="john", user_id=123)

        token_pair = JWTToken(
            access_token=access_token,
            refresh_token=refresh_token
        )

        response = token_pair.encode()
        assert response["scope"] == ""

    def test_expires_in_non_negative(self):
        """Test that expires_in is always non-negative"""
        # Create an access token that's about to expire
        almost_expired = datetime.now(timezone.utc) + timedelta(seconds=1)
        access_token = AccessToken(sub="user123", exp=almost_expired)
        refresh_token = RefreshToken(username="john", user_id=123)

        token_pair = JWTToken(
            access_token=access_token,
            refresh_token=refresh_token
        )

        response = token_pair.encode()
        assert response["expires_in"] >= 0

    def test_is_valid_with_valid_pair(self):
        """Test validation with valid token pair"""
        access_token = AccessToken(sub="user123",exp=datetime.now(timezone.utc) + timedelta(hours=1))
        refresh_token = RefreshToken(username="john", user_id=123,expires_at=datetime.now(timezone.utc) + timedelta(hours=1))

        token_pair = JWTToken(
            access_token=access_token,
            refresh_token=refresh_token
        )

        assert token_pair.is_valid() is True
        assert bool(token_pair) is True

    def test_is_valid_with_invalid_access_token(self):
        """Test validation with invalid access token"""
        access_token = AccessToken(sub="")  # Invalid: no subject
        refresh_token = RefreshToken(username="john", user_id=123)

        token_pair = JWTToken(
            access_token=access_token,
            refresh_token=refresh_token
        )

        assert token_pair.is_valid() is False
        assert bool(token_pair) is False

    def test_is_valid_with_invalid_refresh_token(self):
        """Test validation with invalid refresh token"""
        access_token = AccessToken(sub="user123")
        refresh_token = RefreshToken(username="", user_id=123)  # Invalid: no username

        token_pair = JWTToken(
            access_token=access_token,
            refresh_token=refresh_token
        )

        assert token_pair.is_valid() is False
        assert bool(token_pair) is False

    def test_is_valid_with_both_invalid_tokens(self):
        """Test validation with both tokens invalid"""
        access_token = AccessToken(sub="")
        refresh_token = RefreshToken(username="", user_id=0)

        token_pair = JWTToken(
            access_token=access_token,
            refresh_token=refresh_token
        )

        assert token_pair.is_valid() is False
        assert bool(token_pair) is False