# app/security/auth.py
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from passlib.context import CryptContext
from bson import ObjectId
from app.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_MINUTES
from app.db import get_db, doc_with_id

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def hash_password(p: str) -> str:
    return pwd_context.hash(p)

def create_access_token(data: dict, minutes: int = JWT_EXPIRE_MINUTES) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=minutes)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)):
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
        uid = sub  # stringified ObjectId
    except JWTError:
        raise cred_exc

    db = get_db()
    try:
        user = await db.users.find_one({"_id": ObjectId(uid)})
    except Exception:
        raise cred_exc

    if not user:
        raise cred_exc
    return doc_with_id(user)  # dict with string "id"


# app/security/auth.py  (ADD THESE)
import os, re, secrets
from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- OTP config ---
OTP_TTL_MIN = int(os.getenv("RESET_OTP_EXPIRE_MINUTES", "10"))  # 10 minutes
OTP_LEN = 6

# --- Reset JWT config (for step after OTP is verified) ---
RESET_SECRET = os.getenv("JWT_RESET_SECRET", os.getenv("JWT_SECRET", "changeme"))
RESET_ALG    = os.getenv("JWT_ALGORITHM", "HS256")
RESET_TTL_MIN = int(os.getenv("RESET_TOKEN_EXPIRE_MINUTES", "15"))

def hash_str(s: str) -> str:
    return pwd_context.hash(s)

def verify_str(s: str, h: str) -> bool:
    return pwd_context.verify(s, h)

def generate_otp(length: int = OTP_LEN) -> str:
    # digits only OTP
    return "".join(str(secrets.randbelow(10)) for _ in range(length))

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

