from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from app.auth.routes import router as auth_router
from app.chat.routes import router as chat_router
from app.chat.websocket import router as websocket_router
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Serve uploaded images ──────────────────────────────────────────
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ── Serve frontend static files (CSS, JS, assets) ─────────────────
os.makedirs("frontend", exist_ok=True)
app.mount("/assets", StaticFiles(directory="frontend/assets"), name="assets") if os.path.exists("frontend/assets") else None

# ── Routers ────────────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(websocket_router)

# ── Serve frontend index.html at root ─────────────────────────────
@app.get("/")
def serve_frontend():
    return FileResponse("frontend/index.html")

# ── Catch-all: serve index.html for any unknown route ─────────────
# This handles page refreshes on frontend routes
@app.get("/{full_path:path}")
def catch_all(full_path: str):
    index = "frontend/index.html"
    if os.path.exists(index):
        return FileResponse(index)
    return {"message": "ZapTalk backend running"}