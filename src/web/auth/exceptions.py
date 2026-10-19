
class AuthError(Exception):
    """
    Base exception for authentication/authorization errors.

    Use this as a common parent for auth_old-layer exceptions.
    """


class TokenError(AuthError):
    """
    Base exception for token-related errors.

    Important:
        Do not put raw access/refresh tokens into error messages.
        Tokens are credentials and should not appear in logs.
    """

    def __init__(self, message: str = "Invalid token") -> None:
        super().__init__(message)


class TokenNotFoundError(TokenError):
    """
    Refresh token was not found in token storage.

    Usually happens when:
        - token is unknown;
        - token was already rotated;
        - token was revoked;
        - token storage was cleared.
    """

    def __init__(self) -> None:
        super().__init__("Refresh token not found")


class TokenExpiredError(TokenError):
    """
    Token has expired.
    """

    def __init__(self) -> None:
        super().__init__("Token has expired")


class TokenRevokedError(TokenError):
    """
    Token was revoked manually.

    Example:
        - logout;
        - logout from all devices;
        - password change;
        - user/admin disabled.
    """

    def __init__(self) -> None:
        super().__init__("Token has been revoked")


class TokenUsedError(TokenError):
    """
    Refresh token was already used.

    Useful for refresh-token rotation.
    """

    def __init__(self) -> None:
        super().__init__("Refresh token has already been used")


class TokenSubjectTypeError(TokenError):
    """
    Token subject_type does not match expected realm.

    Example:
        - user refresh token used on admin refresh endpoint;
        - admin token used on user endpoint.
    """

    def __init__(self) -> None:
        super().__init__("Token subject type mismatch")


class InvalidTokenPayloadError(TokenError):
    """
    Token payload is structurally invalid.

    Example:
        - missing sub;
        - missing subject_type;
        - invalid token_type;
        - invalid aud/iss.
    """

    def __init__(self, message: str = "Invalid token payload") -> None:
        super().__init__(message)


class UserNotValidError(AuthError):
    """
    User/admin related to token is no longer valid.

    Example:
        - account was deleted;
        - account was disabled;
        - login no longer exists.
    """

    def __init__(self, username: str | None = None) -> None:
        if username:
            super().__init__(f"User '{username}' is not valid")
        else:
            super().__init__("User is not valid")


class InvalidCredentialsError(AuthError):
    """
    Login or password is invalid.

    Do not specify whether login or password is wrong.
    This prevents account enumeration.
    """

    def __init__(self) -> None:
        super().__init__("Invalid login or password")


class AuthPermissionError(AuthError):
    """
    Authenticated subject does not have required permission/scope.
    """

    def __init__(self, message: str = "Permission denied") -> None:
        super().__init__(message)