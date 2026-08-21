from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field

from app.constants import MAX_CAMERAS_PER_COURT, MIN_CAMERAS_PER_COURT
from app.models import AccessRequestStatus, UserRole


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=255)
    role: Literal[UserRole.athlete, UserRole.scout]


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    is_approved: bool
    avatar_url: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class UserProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=255)
    email: EmailStr | None = None
    avatar_url: str | None = None
    current_password: str | None = None
    new_password: str | None = Field(default=None, min_length=8)


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ForgotPasswordResponse(BaseModel):
    message: str
    reset_token: str | None = None


class ResetPasswordRequest(BaseModel):
    token: str = Field(min_length=10)
    password: str = Field(min_length=8)


class GoogleAuthRequest(BaseModel):
    id_token: str = Field(min_length=20)
    role: Literal[UserRole.athlete, UserRole.scout] = UserRole.athlete


class CourtCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    city_id: int
    address: str | None = None
    camera_count: int = Field(
        default=2, ge=MIN_CAMERAS_PER_COURT, le=MAX_CAMERAS_PER_COURT
    )


class CourtUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    city_id: int | None = None
    address: str | None = None
    camera_count: int | None = Field(
        default=None, ge=MIN_CAMERAS_PER_COURT, le=MAX_CAMERAS_PER_COURT
    )


class CourtResponse(BaseModel):
    id: int
    name: str
    city_id: int | None = None
    city_name: str | None = None
    address: str | None
    is_active: bool
    created_at: datetime
    device_api_key: str | None = None

    model_config = {"from_attributes": True}


class CityCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)


class CityUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=255)
    is_active: bool | None = None


class CityResponse(BaseModel):
    id: int
    name: str
    is_active: bool
    created_at: datetime
    court_count: int = 0

    model_config = {"from_attributes": True}


class DeviceResponse(BaseModel):
    id: int
    court_id: int
    camera_index: int
    name: str
    is_online: bool
    last_heartbeat: datetime | None

    model_config = {"from_attributes": True}


class CourtAccessRequestCreate(BaseModel):
    court_id: int
    play_started_at: datetime
    play_ended_at: datetime


class CourtAccessRequestResponse(BaseModel):
    id: int
    user_id: int
    court_id: int
    status: AccessRequestStatus
    play_started_at: datetime | None = None
    play_ended_at: datetime | None = None
    created_at: datetime
    reviewed_at: datetime | None
    user: UserResponse | None = None
    court: CourtResponse | None = None

    model_config = {"from_attributes": True}


class CourtAccessResponse(BaseModel):
    id: int
    user_id: int
    court_id: int
    granted_at: datetime
    court: CourtResponse | None = None

    model_config = {"from_attributes": True}


class RecordingResponse(BaseModel):
    id: int
    court_id: int
    camera_index: int
    duration_seconds: int
    triggered_at: datetime
    expires_at: datetime
    created_at: datetime
    download_url: str | None = None
    court_name: str | None = None

    model_config = {"from_attributes": True}


class DeviceHeartbeat(BaseModel):
    camera_index: int = Field(ge=MIN_CAMERAS_PER_COURT, le=MAX_CAMERAS_PER_COURT)


class CaptureTriggerRequest(BaseModel):
    court_id: int
    camera_index: int | None = Field(
        default=None, ge=MIN_CAMERAS_PER_COURT, le=MAX_CAMERAS_PER_COURT
    )


class CaptureTriggerResponse(BaseModel):
    message: str
    court_id: int
    court_name: str
    cameras: list[int]
    device_online: bool


class PendingTriggerItem(BaseModel):
    id: int
    camera_index: int
    created_at: datetime


class MessageResponse(BaseModel):
    message: str


class AdminCreateUser(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=255)
    role: Literal[UserRole.athlete, UserRole.scout]


class AdminUpdateUser(BaseModel):
    is_active: bool | None = None
    is_approved: bool | None = None


class PlatformSettingsResponse(BaseModel):
    platform_name: str
    support_email: str
    timezone: str
    language: str
    storage_limit_tb: float
    retention_hours: int

    model_config = {"from_attributes": True}


class PlatformSettingsUpdate(BaseModel):
    platform_name: str | None = Field(default=None, min_length=2, max_length=255)
    support_email: EmailStr | None = None
    timezone: str | None = None
    language: str | None = None
    storage_limit_tb: float | None = Field(default=None, ge=0.1, le=100)
    retention_hours: int | None = Field(default=None, ge=1, le=720)


class ActivityItem(BaseModel):
    message: str
    created_at: datetime
    kind: str


class AdminRecordingResponse(RecordingResponse):
    status: str
