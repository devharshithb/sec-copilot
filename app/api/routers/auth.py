# app/api/routers/auth.py
from datetime import datetime
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr

from app.db import get_db
from app.security.auth import hash_password, verify_password, create_access_token

router = APIRouter(prefix="/auth", tags=["auth"])

class SignupIn(BaseModel):
    email: EmailStr
    password: str

class LoginIn(BaseModel):
    email: EmailStr
    password: str

@router.post("/signup")
async def signup(data: SignupIn):
    db = get_db()
    email = data.email.lower()
    exists = await db.users.find_one({"email": email})
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = {
        "email": email,
        "hashed_password": hash_password(data.password),
        "is_admin": False,
        "created_at": datetime.utcnow().isoformat(),
    }
    res = await db.users.insert_one(user)
    token = create_access_token({"sub": str(res.inserted_id)})
    return {"access_token": token, "token_type": "bearer"}

@router.post("/login")
async def login(data: LoginIn):
    db = get_db()
    email = data.email.lower()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(data.password, user.get("hashed_password", "")):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    token = create_access_token({"sub": str(user["_id"])})
    return {"access_token": token, "token_type": "bearer"}
