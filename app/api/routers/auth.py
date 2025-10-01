# app/api/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId
from datetime import datetime, timedelta

from app.db import get_db  # Motor database
from app.security.auth import (
    hash_password,
    verify_password,
    create_access_token,
    generate_otp,
    hash_str,
    verify_str,
    create_reset_token,
    verify_reset_token,
    OTP_TTL_MIN,
)

router = APIRouter(prefix="/auth", tags=["auth"])

# ---------- Schemas ----------
class SignupIn(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None            # <--- NEW

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class ForgotIn(BaseModel):
    email: EmailStr

class VerifyOtpIn(BaseModel):
    email: EmailStr
    otp: str

class ResetIn(BaseModel):
    token: str
    new_password: str


# ---------- Helpers ----------
def user_public(u: dict) -> dict:
    return {
        "id": str(u["_id"]),
        "email": u.get("email", ""),
        "name": u.get("name", ""),         # <--- include name
        "is_admin": bool(u.get("is_admin", False)),
        "created_at": u.get("created_at"),
    }


# ---------- Signup ----------
@router.post("/signup")
async def signup(data: SignupIn, db: AsyncIOMotorDatabase = Depends(get_db)):
    email = str(data.email).lower()
    existing = await db.users.find_one({"email": email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    now = datetime.utcnow()
    doc = {
        "email": email,
        "name": (data.name or "").strip(),           # <--- store name
        "hashed_password": hash_password(data.password),
        "is_admin": False,
        "created_at": now,
        "updated_at": now,
    }
    res = await db.users.insert_one(doc)
    uid = str(res.inserted_id)

    token = create_access_token({"sub": uid})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user_public({**doc, "_id": res.inserted_id}),
    }


# ---------- Login ----------
@router.post("/login")
async def login(data: LoginIn, db: AsyncIOMotorDatabase = Depends(get_db)):
    email = str(data.email).lower()
    u = await db.users.find_one({"email": email})
    if not u or not verify_password(data.password, u.get("hashed_password", "")):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    token = create_access_token({"sub": str(u["_id"])})
    return {"access_token": token, "token_type": "bearer", "user": user_public(u)}


# ---------- Forgot (step 1: generate & store OTP) ----------
@router.post("/forgot")
async def forgot_password(data: ForgotIn, db: AsyncIOMotorDatabase = Depends(get_db)):
    email = str(data.email).lower()
    u = await db.users.find_one({"email": email})

    # Always return OK to prevent email enumeration
    if not u:
        return {"ok": True}

    otp = generate_otp()           # e.g., "493028"
    otp_hash = hash_str(otp)
    expires_at = datetime.utcnow() + timedelta(minutes=OTP_TTL_MIN)

    await db.users.update_one(
        {"_id": u["_id"]},
        {"$set": {
            "reset": {
                "otp_hash": otp_hash,
                "otp_expires_at": expires_at,
                "attempts": 0,
                "issued_at": datetime.utcnow()
            }
        }}
    )

    # TODO: send OTP via email/SMS in production
    # DEV convenience: return OTP so you can test without email provider
    return {"ok": True, "dev_otp": otp}


# ---------- Verify OTP (step 2: check OTP, issue reset token) ----------
@router.post("/forgot/verify")
async def verify_otp(body: VerifyOtpIn, db: AsyncIOMotorDatabase = Depends(get_db)):
    email = str(body.email).lower()
    otp = body.otp.strip()

    u = await db.users.find_one({"email": email})
    if not u or "reset" not in u:
        # Don’t reveal which part failed
        raise HTTPException(status_code=400, detail="Invalid OTP or expired")

    r = u["reset"]
    if not r or "otp_hash" not in r or "otp_expires_at" not in r:
        raise HTTPException(status_code=400, detail="Invalid OTP or expired")

    # Expiry
    if datetime.utcnow() > r["otp_expires_at"]:
        # consume it
        await db.users.update_one({"_id": u["_id"]}, {"$unset": {"reset": ""}})
        raise HTTPException(status_code=400, detail="Invalid OTP or expired")

    # Attempts limit (optional)
    attempts = int(r.get("attempts", 0))
    if attempts > 5:
        await db.users.update_one({"_id": u["_id"]}, {"$unset": {"reset": ""}})
        raise HTTPException(status_code=400, detail="Too many attempts, request a new OTP")

    # Verify
    if not verify_str(otp, r["otp_hash"]):
        await db.users.update_one({"_id": u["_id"]}, {"$inc": {"reset.attempts": 1}})
        raise HTTPException(status_code=400, detail="Invalid OTP or expired")

    # OTP OK → consume it
    await db.users.update_one({"_id": u["_id"]}, {"$unset": {"reset": ""}})

    # Issue short-lived reset token (JWT)
    reset_token = create_reset_token(str(u["_id"]))
    return {"ok": True, "reset_token": reset_token}


# ---------- Reset (step 3: set new password using reset token) ----------
@router.post("/reset")
async def reset_password(data: ResetIn, db: AsyncIOMotorDatabase = Depends(get_db)):
    try:
        user_id = verify_reset_token(data.token)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")

    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid token subject")

    u = await db.users.find_one({"_id": oid})
    if not u:
        raise HTTPException(status_code=400, detail="Invalid token subject")

    # Update password
    new_hash = hash_password(data.new_password)
    await db.users.update_one({"_id": oid}, {"$set": {"hashed_password": new_hash}})

    # Do NOT auto-login; require explicit login afterwards
    return {"ok": True}
