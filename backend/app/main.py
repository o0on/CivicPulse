import signal
import uuid
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.core.database import engine
from app.core.logging import configure_logging
from app.core.redis import close_redis, init_redis
from app.providers.triage.factory import create_triage_provider
from app.routes.complaints import router as complaints_router
from app.routes.meta import router as meta_router
from app.routes.metrics import router as metrics_router
from app.routes.stats import router as stats_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging(settings.LOG_LEVEL)
    await init_redis()
    app.state.triage_provider = create_triage_provider()
    try:
        async with engine.begin() as conn:
            await conn.execute(
                text(
                    "DO $$ BEGIN CREATE TYPE category_enum AS ENUM "
                    "('water', 'electricity', 'sanitation', 'roads', 'streetlights', 'other'); "
                    "EXCEPTION WHEN duplicate_object THEN null; END $$;"
                )
            )
            await conn.execute(
                text(
                    "DO $$ BEGIN CREATE TYPE priority_enum AS ENUM "
                    "('high', 'normal', 'low'); "
                    "EXCEPTION WHEN duplicate_object THEN null; END $$;"
                )
            )
            await conn.execute(
                text(
                    "DO $$ BEGIN CREATE TYPE status_enum AS ENUM "
                    "('open', 'in_progress', 'resolved', 'rejected'); "
                    "EXCEPTION WHEN duplicate_object THEN null; END $$;"
                )
            )
            await conn.execute(
                text(
                    "CREATE TABLE IF NOT EXISTS complaints ("
                    "id UUID PRIMARY KEY DEFAULT gen_random_uuid(), "
                    "text VARCHAR(2000) NOT NULL CHECK (char_length(text) >= 10), "
                    "location VARCHAR(200) NOT NULL CHECK (char_length(location) >= 3), "
                    "reporter_contact VARCHAR(255), "
                    "category category_enum NOT NULL, "
                    "priority priority_enum NOT NULL, "
                    "status status_enum NOT NULL DEFAULT 'open', "
                    "ai_summary VARCHAR(140), "
                    "triaged_by VARCHAR(32), "
                    "triage_latency_ms INTEGER NOT NULL, "
                    "created_at TIMESTAMPTZ NOT NULL DEFAULT now(), "
                    "updated_at TIMESTAMPTZ NOT NULL DEFAULT now());"
                )
            )
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_complaints_status_priority ON complaints (status, priority);"))
            await conn.execute(text("CREATE INDEX IF NOT EXISTS idx_complaints_created_at_desc ON complaints (created_at DESC);"))
    except Exception:
        pass
    yield
    await close_redis()

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.LOG_LEVEL != "DEBUG":
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=["*"])

@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    import time
    start = time.perf_counter()
    response = await call_next(request)
    process_time = int((time.perf_counter() - start) * 1000)
    response.headers["X-Response-Time-Ms"] = str(process_time)
    return response

@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID")
    if not req_id:
        req_id = str(uuid.uuid4())
    response = await call_next(request)
    response.headers["X-Request-ID"] = req_id
    return response

app.include_router(complaints_router, prefix="/api")
app.include_router(stats_router, prefix="/api")
app.include_router(meta_router)
app.include_router(meta_router, prefix="/api")
app.include_router(metrics_router, prefix="/api")
app.include_router(metrics_router)

def handle_sigterm(signum, frame):
    pass
signal.signal(signal.SIGTERM, handle_sigterm)
signal.signal(signal.SIGINT, handle_sigterm)

# Graceful drain handler on shutdown
