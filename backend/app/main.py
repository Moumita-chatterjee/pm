from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import STATIC_DIR
from app.db import init_db
from app.routers import auth, board, chat, health

app = FastAPI()

init_db()
STATIC_DIR.mkdir(parents=True, exist_ok=True)

# Lets `npm run dev` (localhost:3000) call the backend on :8000 directly
# during frontend iteration, without going through a container rebuild.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(board.router, prefix="/api")
app.include_router(chat.router, prefix="/api")

# Registered last: a catch-all for the built frontend. Anything under /api/*
# above is matched first, so this never shadows an API route.
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
