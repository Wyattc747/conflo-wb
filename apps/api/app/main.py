from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(title="Conflo API", version="0.1.0", lifespan=lifespan)

if settings.SENTRY_DSN:
    sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=0.1)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "service": "conflo-api"}


# Auth middleware
from app.middleware.auth import AuthMiddleware

app.add_middleware(AuthMiddleware)

# Router registration
from app.routers.projects import router as projects_router
from app.routers.assignments import router as assignments_router
from app.routers.billing import router as billing_router
from app.routers.webhooks import router as webhooks_router
from app.routers.auth import router as auth_router
from app.routers.invitations import router as invitations_router
from app.routers.onboarding import router as onboarding_router

app.include_router(projects_router)
app.include_router(assignments_router)
app.include_router(billing_router)
app.include_router(webhooks_router)
app.include_router(auth_router)
app.include_router(invitations_router)
app.include_router(onboarding_router)
