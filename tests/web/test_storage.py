import pytest
from datetime import datetime, timezone, timedelta
import time
from threading import Thread
import concurrent.futures

from src.web.auth.tokens import RefreshToken
from src.web.auth.storage import TokenStoreMemory, TokenNotFoundError
from src.web.auth.tokens import REFRESH_TOKEN_EXPIRE_DAYS


class TestTokenStoreMemory:
    """Test TokenStoreMemory class functionality"""

    def test_singleton_pattern(self):
        """Test that TokenStoreMemory follows singleton pattern"""
        store1 = TokenStoreMemory()
        store2 = TokenStoreMemory()

        assert store1 is store2
        assert id(store1) == id(store2)

    def test_initial_state(self):
        """Test initial state of token store"""
        store = TokenStoreMemory()
        store.clear()  # Ensure clean state

        assert store.count() == 0

    def test_put_and_get_token(self):
        """Test storing and retrieving a token"""
        store = TokenStoreMemory()
        store.clear()

        token = RefreshToken(username="john", user_id=123)

        store.put(token)
        retrieved = store.get(token.token_id)

        assert retrieved == token
        assert retrieved.username == "john"
        assert retrieved.user_id == 123
        assert store.count() == 1

    def test_get_nonexistent_token_raises_error(self):
        """Test getting non-existent token raises TokenNotFoundError"""
        store = TokenStoreMemory()
        store.clear()

        with pytest.raises(TokenNotFoundError) as exc_info:
            store.get("nonexistent-token-id")

        assert exc_info.value.token_id == "nonexistent-token-id"
        assert "not found" in str(exc_info.value).lower()

    def test_delete_token(self):
        """Test token deletion"""
        store = TokenStoreMemory()
        store.clear()

        token = RefreshToken(username="john", user_id=123)
        store.put(token)
        assert store.count() == 1

        store.delete(token.token_id)
        assert store.count() == 0

        # Verify token is gone
        with pytest.raises(TokenNotFoundError):
            store.get(token.token_id)

    def test_delete_nonexistent_token_raises_error(self):
        """Test deleting non-existent token raises TokenNotFoundError"""
        store = TokenStoreMemory()
        store.clear()

        with pytest.raises(TokenNotFoundError) as exc_info:
            store.delete("nonexistent-token-id")

        assert exc_info.value.token_id == "nonexistent-token-id"

    def test_cleanup_expired_tokens(self):
        """Test cleaning up expired tokens"""
        store = TokenStoreMemory()
        store.clear()

        # Valid token (not expired, not used)
        valid_token = RefreshToken(username="john", user_id=123)

        # Expired token
        expired_time = datetime.now(timezone.utc) - timedelta(hours=1)
        expired_token = RefreshToken(
            username="jane",
            user_id=456,
            expires_at=expired_time
        )

        # Used token
        used_token = RefreshToken(username="bob", user_id=789, used=True)

        # Expired and used token
        expired_used_token = RefreshToken(
            username="alice",
            user_id=999,
            expires_at=expired_time,
            used=True
        )

        store.put(valid_token)
        store.put(expired_token)
        store.put(used_token)
        store.put(expired_used_token)

        assert store.count() == 4

        # Cleanup should remove expired and used tokens
        removed_count = store.cleanup_expired_tokens()
        assert removed_count == 3  # expired + used + expired_used
        assert store.count() == 1

        # Verify only valid token remains
        remaining = store.get(valid_token.token_id)
        assert remaining == valid_token

    def test_cleanup_no_tokens_to_remove(self):
        """Test cleanup when no tokens need removal"""
        store = TokenStoreMemory()
        store.clear()

        valid_token1 = RefreshToken(username="john", user_id=123)
        valid_token2 = RefreshToken(username="jane", user_id=456)

        store.put(valid_token1)
        store.put(valid_token2)

        removed_count = store.cleanup_expired_tokens()
        assert removed_count == 0
        assert store.count() == 2

    def test_get_user_tokens(self):
        """Test retrieving tokens by username"""
        store = TokenStoreMemory()
        store.clear()

        token1 = RefreshToken(username="john", user_id=123)
        token2 = RefreshToken(username="john", user_id=123)  # Same user, different token
        token3 = RefreshToken(username="jane", user_id=456)  # Different user
        token4 = RefreshToken(username="john", user_id=123)  # Same user

        for token in [token1, token2, token3, token4]:
            store.put(token)

        john_tokens = store.get_user_tokens("john")
        jane_tokens = store.get_user_tokens("jane")
        bob_tokens = store.get_user_tokens("bob")  # User with no tokens

        assert len(john_tokens) == 3
        assert len(jane_tokens) == 1
        assert len(bob_tokens) == 0

        # Verify all returned tokens belong to the correct user
        assert all(token.username == "john" for token in john_tokens)
        assert all(token.username == "jane" for token in jane_tokens)

    def test_get_user_tokens_empty_store(self):
        """Test getting user tokens from empty store"""
        store = TokenStoreMemory()
        store.clear()

        result = store.get_user_tokens("anyuser")
        assert result == []

    def setup_method(self):
        """Clear token store before each test"""
        store = TokenStoreMemory()
        store.clear()

    def teardown_method(self):
        """Clean up after each test"""
        store = TokenStoreMemory()
        store.clear()

    def test_revoke_user_tokens(self):
        """Test revoking all tokens for a user"""
        store = TokenStoreMemory()
        store.clear()

        token1 = RefreshToken(username="john", user_id=123)
        token2 = RefreshToken(username="john", user_id=123)
        token3 = RefreshToken(username="jane", user_id=456)

        for token in [token1, token2, token3]:
            store.put(token)

        # Verify initial state
        assert not token1.used
        assert not token2.used
        assert not token3.used

        # Revoke John's tokens
        revoked_count = store.revoke_user_tokens("john")
        assert revoked_count == 2

        # Verify John's tokens are marked as used
        john_tokens = store.get_user_tokens("john")
        assert all(token.used for token in john_tokens)

        # Verify Jane's tokens are unaffected
        jane_tokens = store.get_user_tokens("jane")
        assert all(not token.used for token in jane_tokens)

    def test_revoke_user_with_no_tokens(self):
        """Test revoking tokens for user with no tokens"""
        store = TokenStoreMemory()
        store.clear()

        # Add tokens for different user
        token = RefreshToken(username="jane", user_id=456)
        store.put(token)

        revoked_count = store.revoke_user_tokens("nonexistent-user")
        assert revoked_count == 0
        assert store.count() == 1  # Jane's token still there

    def test_count_method(self):
        """Test token counting"""
        store = TokenStoreMemory()
        store.clear()

        assert store.count() == 0

        # Add some tokens
        tokens = [RefreshToken(username=f"user{i}", user_id=i) for i in range(5)]
        for token in tokens:
            store.put(token)

        assert store.count() == 5

        # Remove one token
        store.delete(tokens[0].token_id)
        assert store.count() == 4

    def test_clear_method(self):
        """Test clearing all tokens"""
        store = TokenStoreMemory()
        store.clear()

        # Add tokens
        for i in range(3):
            token = RefreshToken(username=f"user{i}", user_id=i)
            store.put(token)

        assert store.count() == 3

        store.clear()
        assert store.count() == 0

        # Verify no tokens can be retrieved
        with pytest.raises(TokenNotFoundError):
            store.get("any-token-id")

    def test_thread_safety_basic_operations(self):
        """Basic test for thread safety in operations"""
        store = TokenStoreMemory()
        store.clear()

        token = RefreshToken(username="john", user_id=123)

        # These operations should not raise threading errors
        store.put(token)
        retrieved = store.get(token.token_id)
        count = store.count()

        assert retrieved == token
        assert count == 1

    def test_concurrent_operations(self):
        """Test concurrent operations from multiple threads"""
        store = TokenStoreMemory()
        store.clear()

        num_tokens = 100
        tokens = [RefreshToken(username=f"user{i}", user_id=i) for i in range(num_tokens)]

        def put_tokens(tokens_to_put):
            for token in tokens_to_put:
                store.put(token)

        def get_tokens(token_ids):
            for token_id in token_ids:
                try:
                    store.get(token_id)
                except TokenNotFoundError:
                    pass

        def delete_tokens(token_ids):
            for token_id in token_ids:
                try:
                    store.delete(token_id)
                except TokenNotFoundError:
                    pass

        # Test concurrent put operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # Split tokens into chunks for different threads
            chunk_size = num_tokens // 10
            chunks = [tokens[i:i + chunk_size] for i in range(0, num_tokens, chunk_size)]

            futures = [executor.submit(put_tokens, chunk) for chunk in chunks]
            concurrent.futures.wait(futures)

        assert store.count() == num_tokens

        # Test concurrent get operations
        token_ids = [token.token_id for token in tokens]
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            chunk_size = len(token_ids) // 10
            chunks = [token_ids[i:i + chunk_size] for i in range(0, len(token_ids), chunk_size)]

            futures = [executor.submit(get_tokens, chunk) for chunk in chunks]
            concurrent.futures.wait(futures)

        # Test concurrent delete operations
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            chunk_size = len(token_ids) // 10
            chunks = [token_ids[i:i + chunk_size] for i in range(0, len(token_ids), chunk_size)]

            futures = [executor.submit(delete_tokens, chunk) for chunk in chunks]
            concurrent.futures.wait(futures)

        # All tokens should be deleted
        assert store.count() == 0

    def test_token_persistence_in_singleton(self):
        """Test that tokens persist across singleton instances"""
        store1 = TokenStoreMemory()
        store1.clear()

        token = RefreshToken(username="john", user_id=123)
        store1.put(token)

        # Get another instance (should be same singleton)
        store2 = TokenStoreMemory()

        # Token should be accessible from both instances
        assert store1.get(token.token_id) == token
        assert store2.get(token.token_id) == token
        assert store1.count() == store2.count() == 1


class TestTokenNotFoundError:
    """Test TokenNotFoundError exception"""

    def test_exception_creation(self):
        """Test TokenNotFoundError creation and attributes"""
        token_id = "missing-token-123"
        exception = TokenNotFoundError(token_id)

        assert exception.token_id == token_id
        assert str(exception) == f"Refresh token '{token_id}' not found"