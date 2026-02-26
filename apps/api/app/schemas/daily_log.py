from datetime import date, datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.schemas.common import PaginationMeta


class DailyLogCreate(BaseModel):
    log_date: date
    weather_condition: Optional[str] = None
    temp_high: Optional[float] = None
    temp_low: Optional[float] = None
    precipitation: Optional[float] = None
    wind_speed: Optional[float] = None
    humidity: Optional[float] = None
    summary: Optional[str] = None
    work_performed: Optional[str] = None
    materials_received: Optional[str] = None
    equipment_on_site: Optional[str] = None
    visitors: Optional[list[dict]] = None
    safety_incidents: Optional[str] = None
    delays: Optional[str] = None
    extra_work: Optional[str] = None
    manpower: Optional[list[dict]] = None
    status: str = "DRAFT"


class DailyLogUpdate(BaseModel):
    weather_condition: Optional[str] = None
    temp_high: Optional[float] = None
    temp_low: Optional[float] = None
    precipitation: Optional[float] = None
    wind_speed: Optional[float] = None
    humidity: Optional[float] = None
    summary: Optional[str] = None
    work_performed: Optional[str] = None
    materials_received: Optional[str] = None
    equipment_on_site: Optional[str] = None
    visitors: Optional[list[dict]] = None
    safety_incidents: Optional[str] = None
    delays: Optional[str] = None
    extra_work: Optional[str] = None
    manpower: Optional[list[dict]] = None


class DailyLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    project_id: UUID
    log_date: date
    number: str
    weather_data: Optional[dict] = None
    summary: Optional[str] = None
    work_performed: Optional[str] = None
    materials_received: Optional[str] = None
    equipment_on_site: Optional[str] = None
    visitors: Optional[list[dict]] = None
    safety_incidents: Optional[str] = None
    delays_text: Optional[str] = None
    extra_work: Optional[str] = None
    manpower: Optional[list[dict]] = None
    status: str
    created_by: Optional[UUID] = None
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class DailyLogListResponse(BaseModel):
    data: list[DailyLogResponse]
    meta: PaginationMeta
