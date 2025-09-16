# app/api/routers/chat.py
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import anyio
from bson import ObjectId

from app.db import get_db, doc_with_id
from app.security.auth import get_current_user
from src.orchestrator.coordinator import run_conversation

router = APIRouter(prefix="/api", tags=["chat"])

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    mode: str = "assist"
    game_id: Optional[str] = None
    conversation_id: Optional[str] = None  # stringified ObjectId

class ChatResponse(BaseModel):
    conversation_id: str
    steps: List[Dict[str, Any]]
    final: Dict[str, Any]

def json_dumps(obj: Any) -> str:
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)

async def _ensure_conversation(db, user_id: str, conversation_id: Optional[str], title_hint: str) -> dict:
    if conversation_id:
        try:
            oid = ObjectId(conversation_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid conversation id")
        conv = await db.conversations.find_one({"_id": oid})
        if not conv or str(conv.get("owner_id")) != user_id:
            raise HTTPException(status_code=404, detail="Conversation not found")
        return doc_with_id(conv)

    title = (title_hint or "New conversation").strip()[:200]
    conv = {
        "title": title,
        "owner_id": ObjectId(user_id),
        "folder_id": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    res = await db.conversations.insert_one(conv)
    conv = await db.conversations.find_one({"_id": res.inserted_id})
    return doc_with_id(conv)

async def _persist_exchange(db, conv: dict, req: ChatRequest, result: Dict[str, Any]) -> None:
    conv_oid = ObjectId(conv["id"])

    # incoming messages
    to_insert = []
    for m in req.messages:
        if m.role in {"user", "assistant"}:
            to_insert.append({
                "conversation_id": conv_oid,
                "role": m.role,
                "content": m.content,
                "created_at": datetime.utcnow().isoformat(),
            })
    if to_insert:
        await db.messages.insert_many(to_insert)

    # assistant summary as message
    assistant_summary = (result.get("final") or {}).get("summary", "")
    if assistant_summary:
        await db.messages.insert_one({
            "conversation_id": conv_oid,
            "role": "assistant",
            "content": assistant_summary,
            "created_at": datetime.utcnow().isoformat(),
        })

    # trace
    await db.traces.insert_one({
        "conversation_id": conv_oid,
        "steps_json": json_dumps(result.get("steps", [])),
        "final_json": json_dumps(result.get("final", {})),
        "created_at": datetime.utcnow().isoformat(),
    })

    await db.conversations.update_one(
        {"_id": conv_oid},
        {"$set": {"updated_at": datetime.utcnow().isoformat()}}
    )

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, user=Depends(get_current_user)):
    if not req.messages:
        raise HTTPException(status_code=400, detail="messages cannot be empty")

    last_user_msg = next((m.content for m in reversed(req.messages) if m.role == "user"), "New conversation")

    db = get_db()
    conv = await _ensure_conversation(db, user["id"], req.conversation_id, last_user_msg)

    # Orchestrator call; pass plain list of dicts
    result = await anyio.to_thread.run_sync(
        run_conversation,
        [m.dict() for m in req.messages],
        req.mode,
        req.game_id,
    )
    result = result or {}

    await _persist_exchange(db, conv, req, result)

    return ChatResponse(
        conversation_id=conv["id"],
        steps=result.get("steps", []),
        final=result.get("final", {}),
    )
