from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.cleanup import start_scheduler
from app.database import Base, SessionLocal, engine
from app.routers import admin, auth, courts, devices, recordings
from app.routers import access as access_router
from app.platform_settings import ensure_platform_settings
from app.schema_patches import ensure_user_columns
from app.security import ensure_admin_user
from app.storage import ensure_bucket_exists


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_user_columns()
    ensure_bucket_exists()

    db = SessionLocal()
    try:
        ensure_admin_user(db)
        ensure_platform_settings(db)
    finally:
        db.close()

    scheduler = start_scheduler()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Olho no Lance API",
    description="Backend for court recording platform",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(courts.router, prefix="/api")
app.include_router(access_router.router, prefix="/api")
app.include_router(devices.router, prefix="/api")
app.include_router(recordings.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.get("/health")
def health():
    return {"status": "ok", "app": "Olho no Lance"}
