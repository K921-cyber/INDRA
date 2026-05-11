import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from database import Base, engine
from routers import users, query, cases, feeds
from scheduler import start_scheduler, stop_scheduler


# ── Logging ───────────────────────────────────────────────────────────────
logging.basicConfig(
    level   = logging.INFO,
    format  = "%(asctime)s  %(name)-20s  %(levelname)-8s  %(message)s",
    datefmt = "%H:%M:%S",
)


# ── Lifespan ──────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    print("Database ready")
    start_scheduler()
    print("Scheduler running")
    yield
    # Shutdown
    stop_scheduler()
    print("Server stopped cleanly")


# ── App ───────────────────────────────────────────────────────────────────
app = FastAPI(
    title       = "INDRA - India OSINT Intelligence Platform",
    description = "Centralized open-source intelligence platform for India.",
    version     = "2.1.0",
    lifespan    = lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins     = ["*"],
    allow_credentials = True,
    allow_methods     = ["*"],
    allow_headers     = ["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────
app.include_router(users.router, prefix="/api/auth",  tags=["Authentication"])
app.include_router(query.router, prefix="/api/query", tags=["OSINT Queries"])
app.include_router(cases.router, prefix="/api/cases", tags=["Case Management"])
app.include_router(feeds.router, prefix="/api/feeds", tags=["Intelligence Feeds"])

# ── Health ────────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["System"])
def health():
    return {"status": "operational", "platform": "INDRA v2.1"}

# ── Frontend (Step 12 will activate this) ─────────────────────────────────
if os.path.isfile("frontend/index.html"):
    @app.get("/", include_in_schema=False)
    def serve_frontend():
        return FileResponse("frontend/index.html")

    app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
