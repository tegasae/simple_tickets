from typing import Any

from src.domain.repositories.creation_result_repository import CreationKey, CreationResult


class CreationResultMapper:
    RESULT_COLUMNS = ["fingerprint", "status_code", "body", "expires_at"]
    KEY_COLUMNS = ["employee_id", "idempotency_key"]

    @staticmethod
    def row_to_result(row: dict[str, Any]) -> CreationResult:
        return CreationResult(
            fingerprint=row["fingerprint"],
            status_code=row["status_code"],
            body=row["body"],
            expires_at=row["expires_at"],
        )

    @staticmethod
    def row_to_key(row: dict[str, Any]) -> CreationKey:
        return CreationKey(
            employee_id=row["employee_id"],
            key=row["idempotency_key"],
        )

    @staticmethod
    def key_params(key: CreationKey, **values: object) -> dict[str, object]:
        return {
            **values,
            "employee_id": key.employee_id,
            "key": key.key,
        }

    @classmethod
    def completion_params(cls, key: CreationKey, result: CreationResult) -> dict[str, object]:
        return cls.key_params(key, status_code=result.status_code, body=result.body)

    @staticmethod
    def expiry_params(now: float) -> dict[str, float]:
        return {"now": now}
