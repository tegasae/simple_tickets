from datetime import datetime

from src.adapters.repositories.base_repository import BaseRepository
from src.adapters.repositories.gateways.refresh_session_gateway import RefreshSessionGateway
from src.adapters.repositories.mappers.refresh_session_mapper import RefreshSessionMapper
from src.domain.repositories.refresh_session_repository import (
    RefreshSession,
    RefreshSessionRepository,
    SubjectType,
)
from utils.db.connect import Connection


class RefreshSessionRepositorySQLite(BaseRepository, RefreshSessionRepository):
    def __init__(self, connection: Connection) -> None:
        super().__init__(connection)

    def get(self, token_hash: str) -> RefreshSession | None:
        row = self._get_one(
            RefreshSessionGateway.SELECT_BY_HASH,
            var=RefreshSessionMapper.VARS,
            params={"token_hash": token_hash},
        )
        return RefreshSessionMapper.row_to_session(row) if row else None

    def add(self, token_hash: str, session: RefreshSession) -> None:
        self._exec(
            RefreshSessionGateway.INSERT,
            RefreshSessionMapper.session_params(token_hash, session),
        )

    def remove(self, token_hash: str) -> bool:
        result = self._exec(
            RefreshSessionGateway.DELETE_BY_HASH,
            {"token_hash": token_hash},
        )
        return result.rowcount == 1

    def revoke_subject(self, *, subject_type: SubjectType, subject_id: int) -> None:
        self._exec(
            RefreshSessionGateway.DELETE_BY_SUBJECT,
            {"subject_type": subject_type, "subject_id": subject_id},
        )

    def remove_expired(self, *, now: datetime) -> None:
        self._exec(
            RefreshSessionGateway.DELETE_EXPIRED,
            RefreshSessionMapper.expiry_params(now),
        )
