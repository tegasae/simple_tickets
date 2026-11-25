from src.adapters.repositories.base_repository import BaseRepository
from src.adapters.repositories.exceptions import UniqueConstraintError
from src.adapters.repositories.gateways.creation_result_gateway import CreationResultGateway
from src.adapters.repositories.mappers.creation_result_mapper import CreationResultMapper
from src.domain.repositories.creation_result_repository import (
    CreationAlreadyReserved, CreationKey, CreationResult, CreationResultRepository,
)
from utils.db.connect import Connection


class CreationResultRepositorySQLite(BaseRepository, CreationResultRepository):
    def __init__(self, connection: Connection) -> None:
        super().__init__(connection)

    def get(self, key: CreationKey) -> CreationResult | None:
        row = self._get_one(
            CreationResultGateway.SELECT_BY_KEY,
            var=CreationResultMapper.RESULT_COLUMNS,
            params=CreationResultMapper.key_params(key),
        )
        return CreationResultMapper.row_to_result(row) if row else None

    def reserve(self, key: CreationKey, *, fingerprint: str) -> None:
        try:
            self._exec(
                CreationResultGateway.INSERT_RESERVATION,
                CreationResultMapper.key_params(key, fingerprint=fingerprint),
            )
        except UniqueConstraintError as exc:
            raise CreationAlreadyReserved() from exc

    def complete(self, key: CreationKey, *, result: CreationResult) -> None:
        written = self._exec(
            CreationResultGateway.COMPLETE,
            CreationResultMapper.completion_params(key, result),
        )
        if written.rowcount != 1:
            raise RuntimeError("Expected one reserved creation result")

    def forget_expired(self, key: CreationKey, *, now: float) -> None:
        self._exec(
            CreationResultGateway.DELETE_EXPIRED_BY_KEY,
            CreationResultMapper.key_params(key, now=now),
        )

    def pending_deadlines(self) -> list[CreationKey]:
        rows = self._get_many(
            CreationResultGateway.SELECT_PENDING_DEADLINES,
            var=CreationResultMapper.KEY_COLUMNS,
        )
        return [CreationResultMapper.row_to_key(row) for row in rows]

    def set_deadline(self, key: CreationKey, *, expires_at: float) -> None:
        self._exec(
            CreationResultGateway.SET_DEADLINE,
            CreationResultMapper.key_params(key, expires_at=expires_at),
        )

    def prune_expired(self, *, now: float) -> None:
        self._exec(
            CreationResultGateway.DELETE_EXPIRED,
            CreationResultMapper.expiry_params(now),
        )
