# app/security/auth.py
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
import os
import secrets

from app.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES
from app.db import get_db
import bcrypt

# Patch: make passlib not choke on bcrypt >=4
if not hasattr(bcrypt, "__about__"):
    class _About:
        __version__ = getattr(bcrypt, "__version__", "unknown")
    bcrypt.__about__ = _About()


# ========== Password hashing ==========
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def hash_password(p: str) -> str:
    return pwd_context.hash(p)

# ========== Access token (login) ==========
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def create_access_token(data: dict, minutes: int = JWT_EXPIRE_MINUTES) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncIOMotorDatabase = Depends(get_db),     # <--- FIX: use Depends
):
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        sub: Optional[str] = payload.get("sub")
        if sub is None:
            raise cred_exc
        oid = ObjectId(sub)
    except (JWTError, Exception):
        raise cred_exc

    user = await db.users.find_one({"_id": oid})
    if not user:
        raise cred_exc

    # Return dict the rest of the app can use (include name)
    return {
        "id": str(user["_id"]),
        "email": user.get("email", ""),
        "name": user.get("name", ""),           # <--- include name
        "is_admin": bool(user.get("is_admin", False)),
        "created_at": user.get("created_at"),
    }

# ========== OTP + Reset token flow ==========
# OTP config
OTP_TTL_MIN = int(os.getenv("RESET_OTP_EXPIRE_MINUTES", "10"))  # 10 minutes
OTP_LEN = int(os.getenv("RESET_OTP_LENGTH", "6"))

def hash_str(s: str) -> str:
    return pwd_context.hash(s)

def verify_str(s: str, h: str) -> bool:
    return pwd_context.verify(s, h)

def generate_otp(length: int = OTP_LEN) -> str:
    # digits-only OTP
    return "".join(str(secrets.randbelow(10)) for _ in range(length))

# Reset token config (short-lived JWT used after OTP passes)
RESET_SECRET = os.getenv("JWT_RESET_SECRET", JWT_SECRET)
RESET_ALG = os.getenv("JWT_ALGORITHM", JWT_ALGORITHM)
RESET_TTL_MIN = int(os.getenv("RESET_TOKEN_EXPIRE_MINUTES", "15"))

def create_reset_token(user_id: str) -> str:
    now = datetime.utcnow()
    payload = {
        "sub": user_id,
        "typ": "pwd_reset",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=RESET_TTL_MIN)).timestamp()),
    }
    return jwt.encode(payload, RESET_SECRET, algorithm=RESET_ALG)

def verify_reset_token(token: str) -> str:
    data = jwt.decode(token, RESET_SECRET, algorithms=[RESET_ALG])
    if data.get("typ") != "pwd_reset":
        raise ValueError("Invalid token type")
    return str(data["sub"])
