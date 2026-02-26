import uuid

from pydantic import BaseModel


class CompanyProfileUpdate(BaseModel):
    name: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    zip_code: str | None = None
    phone: str | None = None
    license_numbers: dict | None = None
    timezone: str | None = None


class UserProfileUpdate(BaseModel):
    name: str | None = None
    phone: str | None = None
    title: str | None = None


class CostCodeSelection(BaseModel):
    template: str  # "csi_masterformat" | "custom" | "skip"
    custom_codes: list[dict] | None = None  # If template == "custom"


class FirstProjectCreate(BaseModel):
    name: str
    project_number: str | None = None
    address: str | None = None
    project_type: str = "COMMERCIAL"
    contract_value: float | None = None
    phase: str = "BIDDING"  # BIDDING or ACTIVE


class InviteTeamMember(BaseModel):
    email: str
    permission_level: str = "USER"  # MANAGEMENT | USER


class InviteTeamRequest(BaseModel):
    members: list[InviteTeamMember]


class InviteSubEntry(BaseModel):
    company_name: str
    contact_email: str
    trade: str | None = None


class InviteSubRequest(BaseModel):
    subs: list[InviteSubEntry]
