

from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel


from src.web.dependencies.auth import require_current_admin


router = APIRouter(prefix="/admin/new", tags=["new approcach"], dependencies=[])


class ClientCreateRequest(BaseModel):
    name: str
    email: str = ""
    address: str = ""
    phone: str = ""


class ClientUpdateContactRequest(BaseModel):
    email: str = ""
    address: str = ""
    phone: str = ""




@router.post("/", response_model=None)
def new(
    actor_admin_id: int = Depends(require_current_admin),
):

        return jsonable_encoder({"new":1,"actor":actor_admin_id})
