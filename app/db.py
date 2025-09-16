# app/db.py
from typing import AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from bson import ObjectId

from app.config import MONGODB_URI, MONGODB_DB

_client: AsyncIOMotorClient | None = None
_db: AsyncIOMotorDatabase | None = None

def get_client() -> AsyncIOMotorClient:
    global _client
    if _client is None:
        _client = AsyncIOMotorClient(MONGODB_URI)
    return _client

def get_db() -> AsyncIOMotorDatabase:
    global _db
    if _db is None:
        _db = get_client()[MONGODB_DB]
    return _db

# ---- helpers to normalize IDs ----
def doc_with_id(doc: dict | None) -> dict | None:
    if not doc:
        return doc
    out = dict(doc)
    if "_id" in out:
        out["id"] = str(out["_id"])
        del out["_id"]
    for k in ("owner_id", "folder_id", "conversation_id"):
        if k in out and isinstance(out[k], ObjectId):
            out[k] = str(out[k])
    return out

def docs_with_id(docs: list[dict]) -> list[dict]:
    return [doc_with_id(d) for d in docs]

# ---- idempotent index creator ----
async def ensure_index(
    coll,
    keys: list[tuple[str, int]],
    *,
    name: str,
    unique: bool = False
):
    """
    Ensure an index with specific keys/options exists.
    If same key pattern exists with different options, drop+recreate.
    """
    canonical_name = "_".join(f"{k}_{v}" for k, v in keys)
    existing = await coll.index_information()
    match_name = None
    for idx_name, meta in existing.items():
        key_list = meta.get("key") or []
        if key_list == keys:
            match_name = idx_name
            if bool(meta.get("unique")) == bool(unique):
                return
            await coll.drop_index(idx_name)
            break
    await coll.create_index(keys, name=name or canonical_name, unique=unique)

async def init_db() -> None:
    """
    Create indexes safely (idempotent).
    """
    db = get_db()
    await ensure_index(db.users, [("email", 1)], name="uq_users_email", unique=True)
    await ensure_index(db.conversations, [("owner_id", 1)], name="ix_conversations_owner")
    await ensure_index(db.conversations, [("updated_at", -1)], name="ix_conversations_updated_at_desc")
    await ensure_index(db.messages, [("conversation_id", 1), ("created_at", 1)], name="ix_messages_conv_created")
    await ensure_index(db.folders, [("owner_id", 1)], name="ix_folders_owner")
    await ensure_index(db.traces, [("conversation_id", 1), ("created_at", 1)], name="ix_traces_conv_created")

# FastAPI dependency if you want DI-style access
async def get_db_dep() -> AsyncGenerator[AsyncIOMotorDatabase, None]:
    yield get_db()
