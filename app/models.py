# app/models.py
from __future__ import annotations
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, EmailStr

# ---- Auth models ----
class SignupIn(BaseModel):
    email: EmailStr
    password: str

class LoginIn(BaseModel):
    email: EmailStr
    password: str

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

# ---- Folder models ----
class FolderIn(BaseModel):
    name: str

# ---- Conversation models ----
class ConversationIn(BaseModel):
    title: str
    folder_id: Optional[str] = None

class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    mode: str = "assist"
    game_id: Optional[str] = None
    conversation_id: Optional[str] = None  # Mongo ObjectId (string)

class ChatResponse(BaseModel):
    conversation_id: str
    steps: List[Dict[str, Any]]
    final: Dict[str, Any]
