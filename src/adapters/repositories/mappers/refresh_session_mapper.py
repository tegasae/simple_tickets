import json
from datetime import UTC, datetime

from src.domain.repositories.refresh_session_repository import RefreshSession


class RefreshSessionMapper:
    VARS = [
        "account_id",
        "subject_id",
        "subject_type",
        "username",
        "created_at",
        "expires_at",
        "scope",
    ]

    @staticmethod
    def row_to_session(row: dict) -> RefreshSession:
        return RefreshSession(
            account_id=row["account_id"],
            subject_id=row["subject_id"],
            subject_type=row["subject_type"],
            username=row["username"],
            created_at=datetime.fromtimestamp(row["created_at"], UTC),
            expires_at=datetime.fromtimestamp(row["expires_at"], UTC),
            scope=tuple(json.loads(row["scope"])),
        )

    @staticmethod
    def session_params(token_hash: str, session: RefreshSession) -> dict[str, str | int | float]:
        return {
            "token_hash": token_hash,
            "account_id": session.account_id,
            "subject_id": session.subject_id,
            "subject_type": session.subject_type,
            "username": session.username,
            "created_at": session.created_at.timestamp(),
            "expires_at": session.expires_at.timestamp(),
            "scope": json.dumps(session.scope),
        }

    @staticmethod
    def expiry_params(now: datetime) -> dict[str, float]:
        return {"now": now.timestamp()}
