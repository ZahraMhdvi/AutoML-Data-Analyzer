import re
import sqlite3

from fastapi import APIRouter, Depends

from ml_engine.errors import AppError
from pydantic import BaseModel

from api.core.auth import (
    hash_password,
    verify_password,
    create_session,
    delete_session,
    get_current_user,
)
from api.core.db import connect, now_iso


router = APIRouter(prefix="/api/auth", tags=["auth"])


EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class SignupRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


def _public_user(user):
    return {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "created_at": user["created_at"],
        "locale": (user["locale"] if "locale" in (user.keys() if hasattr(user, "keys") else []) else None),
    }


SUPPORTED_LOCALES = ("en-US", "fa-IR")


class PreferencesRequest(BaseModel):
    locale: str


@router.post("/signup")
def signup(body: SignupRequest):

    name = body.name.strip()
    email = body.email.strip().lower()

    if len(name) < 2:
        raise AppError("AUTH_NAME_TOO_SHORT")

    if not EMAIL_PATTERN.match(email):
        raise AppError("AUTH_INVALID_EMAIL")

    if len(body.password) < 6:
        raise AppError("AUTH_PASSWORD_TOO_SHORT")

    try:
        with connect() as conn:
            cursor = conn.execute(
                "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (name, email, hash_password(body.password), now_iso())
            )
            user_id = cursor.lastrowid
            user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    except sqlite3.IntegrityError:
        raise AppError("AUTH_EMAIL_EXISTS", status=409)

    return {
        "token": create_session(user_id),
        "user": _public_user(user),
    }


@router.post("/login")
def login(body: LoginRequest):

    email = body.email.strip().lower()

    with connect() as conn:
        user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()

    if user is None or not verify_password(body.password, user["password_hash"]):
        raise AppError("AUTH_INVALID_CREDENTIALS", status=401)

    return {
        "token": create_session(user["id"]),
        "user": _public_user(user),
    }


@router.post("/logout")
def logout(user=Depends(get_current_user)):

    delete_session(user["token"])

    return {"success": True}


@router.get("/me")
def me(user=Depends(get_current_user)):

    return {"user": _public_user(user)}


@router.patch("/me/preferences")
def update_preferences(body: PreferencesRequest, user=Depends(get_current_user)):

    locale = body.locale if body.locale in SUPPORTED_LOCALES else "en-US"
    with connect() as conn:
        conn.execute("UPDATE users SET locale = ? WHERE id = ?", (locale, user["id"]))
        row = conn.execute("SELECT * FROM users WHERE id = ?", (user["id"],)).fetchone()
    return {"user": _public_user(row)}
