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
from app.routers.daily_logs import router as daily_logs_router
from app.routers.rfis import gc_router as rfis_gc_router, sub_router as rfis_sub_router
from app.routers.comments import gc_router as comments_gc_router, sub_router as comments_sub_router
from app.routers.budget import router as budget_router
from app.routers.pay_apps import gc_router as pay_apps_gc_router, sub_router as pay_apps_sub_router, owner_router as pay_apps_owner_router
from app.routers.change_orders import gc_router as cos_gc_router, sub_router as cos_sub_router, owner_router as cos_owner_router
from app.routers.submittals import gc_router as submittals_gc_router, sub_router as submittals_sub_router
from app.routers.transmittals import gc_router as transmittals_gc_router
from app.routers.punch_list import gc_router as punch_gc_router, sub_router as punch_sub_router, owner_router as punch_owner_router
from app.routers.inspections import gc_router as inspections_gc_router, template_router as inspection_templates_router
from app.routers.schedule import gc_router as schedule_gc_router, sub_router as schedule_sub_router, owner_router as schedule_owner_router
# Sprint 8
from app.routers.meetings import gc_router as meetings_gc_router
from app.routers.todos import gc_router as todos_gc_router, sub_router as todos_sub_router
from app.routers.procurement import gc_router as procurement_gc_router
from app.routers.drawings import gc_router as drawings_gc_router, sub_router as drawings_sub_router, owner_router as drawings_owner_router
from app.routers.documents import gc_router as documents_gc_router, sub_router as documents_sub_router
from app.routers.photos import gc_router as photos_gc_router, sub_router as photos_sub_router
from app.routers.bids import gc_router as bids_gc_router, sub_router as bids_sub_router
# Sprint 9
from app.routers.files import gc_router as files_gc_router, sub_router as files_sub_router, owner_router as files_owner_router
from app.routers.integrations import gc_router as integrations_gc_router
from app.routers.notifications import gc_router as notifications_gc_router, sub_router as notifications_sub_router, owner_router as notifications_owner_router

app.include_router(projects_router)
app.include_router(assignments_router)
app.include_router(billing_router)
app.include_router(webhooks_router)
app.include_router(auth_router)
app.include_router(invitations_router)
app.include_router(onboarding_router)
app.include_router(daily_logs_router)
app.include_router(rfis_gc_router)
app.include_router(rfis_sub_router)
app.include_router(comments_gc_router)
app.include_router(comments_sub_router)
app.include_router(budget_router)
app.include_router(pay_apps_gc_router)
app.include_router(pay_apps_sub_router)
app.include_router(pay_apps_owner_router)
app.include_router(cos_gc_router)
app.include_router(cos_sub_router)
app.include_router(cos_owner_router)
# Sprint 7
app.include_router(submittals_gc_router)
app.include_router(submittals_sub_router)
app.include_router(transmittals_gc_router)
app.include_router(punch_gc_router)
app.include_router(punch_sub_router)
app.include_router(punch_owner_router)
app.include_router(inspection_templates_router)
app.include_router(inspections_gc_router)
app.include_router(schedule_gc_router)
app.include_router(schedule_sub_router)
app.include_router(schedule_owner_router)
# Sprint 8
app.include_router(meetings_gc_router)
app.include_router(todos_gc_router)
app.include_router(todos_sub_router)
app.include_router(procurement_gc_router)
app.include_router(drawings_gc_router)
app.include_router(drawings_sub_router)
app.include_router(drawings_owner_router)
app.include_router(documents_gc_router)
app.include_router(documents_sub_router)
app.include_router(photos_gc_router)
app.include_router(photos_sub_router)
app.include_router(bids_gc_router)
app.include_router(bids_sub_router)
# Sprint 9
app.include_router(files_gc_router)
app.include_router(files_sub_router)
app.include_router(files_owner_router)
app.include_router(integrations_gc_router)
app.include_router(notifications_gc_router)
app.include_router(notifications_sub_router)
app.include_router(notifications_owner_router)
