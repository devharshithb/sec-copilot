# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from app.api.routers.chat import router as chat_router
from app.api.routers.auth import router as auth_router
from app.api.routers.data import router as data_router
from app.db import init_db

def add_middlewares(app: FastAPI):
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],   # tighten in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

def add_routers(app: FastAPI):
    app.include_router(auth_router)
    app.include_router(data_router)
    app.include_router(chat_router)

def mount_static(app: FastAPI):
    static_dir = os.path.join(os.path.dirname(__file__), "ui", "web")
    if os.path.isdir(static_dir):
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="ui")

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()   # <- important: create indexes on startup
    yield
    # optional: close clients etc.

def create_app() -> FastAPI:
    app = FastAPI(title="SEC-COPILOT", version="0.1.0", lifespan=lifespan)
    add_middlewares(app)
    add_routers(app)
    mount_static(app)
    return app

app = create_app()
