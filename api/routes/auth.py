import re
import sqlite3

from fastapi import APIRouter, Depends, HTTPException
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
    }


@router.post("/signup")
def signup(body: SignupRequest):

    name = body.name.strip()
    email = body.email.strip().lower()

    if len(name) < 2:
        raise HTTPException(400, "نام باید حداقل ۲ حرف باشد")

    if not EMAIL_PATTERN.match(email):
        raise HTTPException(400, "ایمیل وارد شده معتبر نیست")

    if len(body.password) < 6:
        raise HTTPException(400, "رمز عبور باید حداقل ۶ کاراکتر باشد")

    try:
        with connect() as conn:
            cursor = conn.execute(
                "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (name, email, hash_password(body.password), now_iso())
            )
            user_id = cursor.lastrowid
            user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()

    except sqlite3.IntegrityError:
        raise HTTPException(409, "با این ایمیل قبلاً حساب ساخته شده است؛ وارد شوید")

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
        raise HTTPException(401, "ایمیل یا رمز عبور اشتباه است")

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
