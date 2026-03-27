from typing import Optional

from flask import Response, redirect, session, url_for
from werkzeug.security import check_password_hash, generate_password_hash


def hash_password(password: str) -> str:
    return generate_password_hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return check_password_hash(hashed, password)


def require_login() -> Optional[Response]:
    if "user_id" not in session:
        return redirect(url_for("signin"))
    return None