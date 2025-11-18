class TokenNotFoundError(Exception):
    """Custom exception for token not found"""
    def __init__(self, token_id: str):
        super().__init__(f"Refresh token '{token_id}' not found")


class TokenExpiredError(Exception):

    def __init__(self, token_id: str):
        super().__init__(f"Token '{token_id}' is expired")


class TokenError(Exception):
    def __init__(self, token_id: str):
        super().__init__(f"Token '{token_id}' is wrong")


class UserNotValidError(Exception):
    def __init__(self, user: str):
        super().__init__(f"Token '{user}' is wrong")
