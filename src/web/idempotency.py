"""Execute a keyed creation once, using the service's UnitOfWork."""
from collections.abc import Callable
from datetime import UTC, datetime
import hmac
import json
import logging
from typing import Annotated, Protocol, TypeVar

from fastapi import Depends, Header, HTTPException, Request, Response
from pydantic import BaseModel

from src.adapters.repositories.exceptions import PersistenceError, TransientPersistenceError
from src.domain.repositories.creation_result_repository import (
    CreationAlreadyReserved, CreationKey, CreationResult,
)
from src.domain.uow.unit_of_work import UnitOfWork
from src.domain.value_objects import (
    Address, Description, Email, Login, Name, Phone, ValueObject,
)
from src.web.dependencies.services import get_settings
from src.web.models.clients import ClientCreateRequest
from utils.db.exceptions import DBOperationError

logger = logging.getLogger(__name__)
RESULT_TTL = 24 * 60 * 60
T = TypeVar("T", bound=BaseModel)
ResponseT = TypeVar("ResponseT", bound=BaseModel, covariant=True)


class CreationOperation(Protocol[ResponseT]):
    """Create a resource or check access to the stored result of that creation."""

    def authorize_replay(self) -> None: ...

    def execute(self, *, join_transaction: bool) -> ResponseT: ...


def timestamp() -> float:
    return datetime.now(UTC).timestamp()


def get_idempotency_key(
    request: Request,
    key: Annotated[str | None, Header(
        alias="Idempotency-Key", min_length=1, max_length=128, pattern=r"^[!-~]+$",
        description="Optional key for replaying a successful creation within 24 hours.",
    )] = None,
) -> str | None:
    if len(request.headers.getlist("Idempotency-Key")) > 1:
        raise HTTPException(status_code=422, detail="Supply at most one Idempotency-Key")
    return key


IdempotencyKey = Annotated[str | None, Depends(get_idempotency_key)]


def _fingerprint(
    request: Request, payload: BaseModel, *, command: str, target_id: int | None,
) -> str:
    body = payload.model_dump(mode="json")
    domain_fields: dict[str, type[ValueObject[str]]] = {
        "name": Name,
        "first_name": Name,
        "last_name": Name,
        "login": Login,
        "email": Email,
        "phone": Phone,
        "address": Address,
    }
    if isinstance(payload, ClientCreateRequest):
        domain_fields["description"] = Description

    for field, value_type in domain_fields.items():
        value = body.get(field)
        if isinstance(value, str) and value:
            try:
                body[field] = value_type(value).value
            except ValueError:
                # Keep invalid input distinct for the normal validation path.
                pass

    # These API arrays become sets in the business commands.
    for field in ("roles", "permissions"):
        if isinstance(body.get(field), list):
            body[field] = sorted(set(body[field]))
    canonical = json.dumps(
        [command, target_id, body], ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    )
    seed = get_settings(request).SECRET_KEY.encode()
    fingerprint_key = hmac.digest(seed, b"simple_tickets/creation_fingerprint/v2", "sha256")
    return hmac.new(fingerprint_key, canonical.encode(), "sha256").hexdigest()


def _replay(
    record: CreationResult, fingerprint: str, authorize: Callable[[], object],
) -> CreationResult:
    authorize()
    if not hmac.compare_digest(record.fingerprint, fingerprint):
        raise HTTPException(status_code=409, detail="Idempotency-Key already used for a different request")
    if record.body is None or record.status_code is None:
        raise TransientPersistenceError("Creation result is unavailable")
    return record


def _maintain(uow: UnitOfWork) -> None:
    try:
        with uow:
            # A returned row is already committed. Start its retention only
            # after observing that commit, including after a process restart.
            pending = uow.creation_results.pending_deadlines()
            if not pending:
                return
            now = timestamp()
            for key in pending:
                uow.creation_results.set_deadline(key, expires_at=now + RESULT_TTL)
            uow.creation_results.prune_expired(now=now)
    except (DBOperationError, PersistenceError):
        # The business operation and response are already durable. The next
        # successful keyed request can perform maintenance.
        logger.warning("Creation result retention maintenance deferred")


def create_response(
    *,
    request: Request,
    idempotency_key: str | None,
    uow: UnitOfWork,
    employee_id: int,
    command: str,
    payload: BaseModel,
    status_code: int,
    operation: CreationOperation[T],
    target_id: int | None = None,
) -> T | Response:
    if idempotency_key is None:
        return operation.execute(join_transaction=False)

    key = CreationKey(employee_id=employee_id, key=idempotency_key)
    fingerprint = _fingerprint(request, payload, command=command, target_id=target_id)
    try:
        with uow:
            now = timestamp()
            record = uow.creation_results.get(key)
            if record is not None and (record.expires_at is None or record.expires_at > now):
                result = _replay(record, fingerprint, operation.authorize_replay)
            else:
                if record is not None:
                    uow.creation_results.forget_expired(key, now=now)
                # Claim before any business write, so an entity-level unique
                # constraint cannot hide an already processed duplicate.
                uow.creation_results.reserve(key, fingerprint=fingerprint)
                data = operation.execute(join_transaction=True)
                result = CreationResult(fingerprint, status_code, data.model_dump_json(by_alias=True))
                uow.creation_results.complete(key, result=result)
    except CreationAlreadyReserved:
        # The failed transaction has rolled back. Only read the result of the
        # committed operation; leave another HTTP attempt to the caller.
        with uow:
            record = uow.creation_results.get(key)
            if record is None or (record.expires_at is not None and record.expires_at <= timestamp()):
                raise TransientPersistenceError("Creation result is unavailable")
            result = _replay(record, fingerprint, operation.authorize_replay)

    _maintain(uow)
    return Response(result.body, status_code=result.status_code, media_type="application/json")
