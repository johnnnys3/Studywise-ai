from fastapi import APIRouter, Depends

from app.api.deps import get_current_user


router = APIRouter()


@router.get("/me")
def me(current_user: dict = Depends(get_current_user)) -> dict:
    return {
        "id": current_user["id"],
        "name": current_user["name"],
        "email": current_user["email"],
        "created_at": current_user["created_at"],
    }
