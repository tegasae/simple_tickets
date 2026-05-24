

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel


from src.web.dependencies.auth import require_current_admin, get_current_admin, get_user_id_from_request

router = APIRouter(prefix="/admin/new", tags=["new approcach"], dependencies=[Depends(get_current_admin)])


class ClientCreateRequest(BaseModel):
    name: str
    email: str = ""
    address: str = ""
    phone: str = ""


class ClientUpdateContactRequest(BaseModel):
    email: str = ""
    address: str = ""
    phone: str = ""




@router.post("/admin-id", response_model=None)
def new(
    actor_admin_id: int = Depends(get_user_id_from_request),
):

        return jsonable_encoder({"new":1,"actor":actor_admin_id})


@router.post("/without", response_model=None)
def new(

):

        return jsonable_encoder({"new":2})


