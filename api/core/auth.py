
import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from fastapi import Header, HTTPException

from api.core.db import connect, now_iso


PBKDF2_ITERATIONS = 200_000

SESSION_DAYS = 30


def hash_password(password):

    salt = secrets.token_hex(16)

    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ITERATIONS
    ).hex()

    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt}${digest}"


def verify_password(password, stored):

    try:
        _, iterations, salt, digest = stored.split("$")
    except ValueError:
        return False

    candidate = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        int(iterations)
    ).hex()

    return hmac.compare_digest(candidate, digest)


def _token_hash(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_session(user_id):

    token = secrets.token_urlsafe(32)

    expires = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)

    with connect() as conn:
        conn.execute(
            "INSERT INTO sessions (token_hash, user_id, created_at, expires_at) VALUES (?, ?, ?, ?)",
            (_token_hash(token), user_id, now_iso(), expires.replace(microsecond=0).isoformat())
        )

    return token


def delete_session(token):

    with connect() as conn:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (_token_hash(token),))


def _extract_token(authorization):

    if not authorization:
        return None

    scheme, _, token = authorization.partition(" ")

    if scheme.lower() != "bearer" or not token:
        return None

    return token.strip()


def get_current_user(authorization: str = Header(default=None)):

    token = _extract_token(authorization)

    if not token:
        raise HTTPException(status_code=401, detail="برای ادامه وارد حساب کاربری شوید")

    with connect() as conn:

        row = conn.execute(
            """
            SELECT users.id, users.name, users.email, users.created_at, sessions.expires_at
            FROM sessions JOIN users ON users.id = sessions.user_id
            WHERE sessions.token_hash = ?
            """,
            (_token_hash(token),)
        ).fetchone()

    if row is None:
        raise HTTPException(status_code=401, detail="نشست شما منقضی شده است؛ دوباره وارد شوید")

    if row["expires_at"] < now_iso():
        delete_session(token)
        raise HTTPException(status_code=401, detail="نشست شما منقضی شده است؛ دوباره وارد شوید")

    return {
        "id": row["id"],
        "name": row["name"],
        "email": row["email"],
        "created_at": row["created_at"],
        "token": token,
    }
