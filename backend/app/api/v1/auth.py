from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, EmailStr, Field

from app.core.security import create_access_token, hash_password, verify_password
from app.storage import store


router = APIRouter()


class RegisterRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    password: str


def public_user(user: dict) -> dict:
    return {"id": user["id"], "name": user["name"], "email": user["email"], "created_at": user["created_at"]}


@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest) -> dict:
    if store.find("users", email=payload.email.lower()):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    if find_user_by_name(payload.name):
        raise HTTPException(status_code=409, detail="An account with this name already exists.")
    user = store.insert(
        "users",
        {
            "name": payload.name.strip(),
            "email": payload.email.lower(),
            "hashed_password": hash_password(payload.password),
        },
    )
    return {"access_token": create_access_token(user["id"]), "token_type": "bearer", "user": public_user(user)}


@router.post("/login")
def login(payload: LoginRequest) -> dict:
    user = find_user_by_name_and_password(payload.name, payload.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid name or password.")
    return {"access_token": create_access_token(user["id"]), "token_type": "bearer", "user": public_user(user)}


def find_user_by_name(name: str) -> dict | None:
    normalized_name = name.strip().lower()
    for user in store.all("users"):
        if str(user.get("name", "")).strip().lower() == normalized_name:
            return user
    return None


def find_user_by_name_and_password(name: str, password: str) -> dict | None:
    normalized_name = name.strip().lower()
    for user in store.all("users"):
        if str(user.get("name", "")).strip().lower() == normalized_name and verify_password(password, user["hashed_password"]):
            return user
    return None
