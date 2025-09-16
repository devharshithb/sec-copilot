# app/api/routers/data.py
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from bson import ObjectId

from app.db import get_db, doc_with_id, docs_with_id
from app.security.auth import get_current_user

router = APIRouter(prefix="/data", tags=["data"])

# ----- Folders -----
class FolderIn(BaseModel):
    name: str

@router.post("/folders")
async def create_folder(payload: FolderIn, user=Depends(get_current_user)):
    db = get_db()
    folder = {
        "name": payload.name.strip() or "Untitled",
        "owner_id": ObjectId(user["id"]),
        "created_at": datetime.utcnow().isoformat(),
    }
    res = await db.folders.insert_one(folder)
    created = await db.folders.find_one({"_id": res.inserted_id})
    return doc_with_id(created)

@router.get("/folders")
async def list_folders(user=Depends(get_current_user)):
    db = get_db()
    cur = db.folders.find({"owner_id": ObjectId(user["id"])}).sort([("_id", -1)])
    items = await cur.to_list(1000)
    return docs_with_id(items)

# ----- Conversations -----
class ConversationIn(BaseModel):
    title: str
    folder_id: str | None = None

@router.post("/conversations")
async def create_conversation(payload: ConversationIn, user=Depends(get_current_user)):
    db = get_db()
    folder_oid = None
    if payload.folder_id:
        try:
            folder_oid = ObjectId(payload.folder_id)
        except Exception:
            raise HTTPException(400, "Invalid folder id")
        f = await db.folders.find_one({"_id": folder_oid})
        if not f or str(f["owner_id"]) != user["id"]:
            raise HTTPException(404, "Folder not found")

    conv = {
        "title": (payload.title or "New conversation").strip()[:200],
        "owner_id": ObjectId(user["id"]),
        "folder_id": folder_oid,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    res = await db.conversations.insert_one(conv)
    created = await db.conversations.find_one({"_id": res.inserted_id})
    return doc_with_id(created)

@router.get("/conversations")
async def list_conversations(user=Depends(get_current_user)):
    db = get_db()
    cur = db.conversations.find({"owner_id": ObjectId(user["id"])}).sort([("updated_at", -1)])
    items = await cur.to_list(1000)
    return docs_with_id(items)
