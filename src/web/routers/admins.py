from fastapi import APIRouter

router = APIRouter(
    prefix="/admins",
    tags=["admins"],
    responses={404: {"description": "Not found"}},
)

@router.get("/")
async def read_admins():
    return {}
