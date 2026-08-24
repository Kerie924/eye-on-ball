import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    athlete = "athlete"
    scout = "scout"


class AccessRequestStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_approved: Mapped[bool] = mapped_column(Boolean, default=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    reset_token: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    reset_token_expires: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    access_requests: Mapped[list["CourtAccessRequest"]] = relationship(
        back_populates="user",
        foreign_keys="CourtAccessRequest.user_id",
    )
    court_accesses: Mapped[list["CourtAccess"]] = relationship(
        back_populates="user",
        foreign_keys="CourtAccess.user_id",
    )


class City(Base):
    __tablename__ = "cities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    courts: Mapped[list["Court"]] = relationship(back_populates="city")


class Court(Base):
    __tablename__ = "courts"
    __table_args__ = (UniqueConstraint("city_id", "name"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    city_id: Mapped[int | None] = mapped_column(ForeignKey("cities.id"), index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    device_api_key: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    city: Mapped["City | None"] = relationship(back_populates="courts")
    devices: Mapped[list["Device"]] = relationship(back_populates="court")
    recordings: Mapped[list["Recording"]] = relationship(back_populates="court")
    access_requests: Mapped[list["CourtAccessRequest"]] = relationship(
        back_populates="court"
    )
    court_accesses: Mapped[list["CourtAccess"]] = relationship(back_populates="court")


class Device(Base):
    __tablename__ = "devices"
    __table_args__ = (UniqueConstraint("court_id", "camera_index"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    court_id: Mapped[int] = mapped_column(ForeignKey("courts.id"), index=True)
    camera_index: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(255))
    is_online: Mapped[bool] = mapped_column(Boolean, default=False)
    last_heartbeat: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    court: Mapped["Court"] = relationship(back_populates="devices")
    recordings: Mapped[list["Recording"]] = relationship(back_populates="device")


class CourtAccessRequest(Base):
    __tablename__ = "court_access_requests"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    court_id: Mapped[int] = mapped_column(ForeignKey("courts.id"), index=True)
    status: Mapped[AccessRequestStatus] = mapped_column(
        Enum(AccessRequestStatus), default=AccessRequestStatus.pending, index=True
    )
    # Athlete play window — used to filter which clips they can see after approval
    play_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    play_ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    reviewed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    user: Mapped["User"] = relationship(
        back_populates="access_requests", foreign_keys=[user_id]
    )
    court: Mapped["Court"] = relationship(back_populates="access_requests")


class CourtAccess(Base):
    __tablename__ = "court_access"
    __table_args__ = (UniqueConstraint("user_id", "court_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    court_id: Mapped[int] = mapped_column(ForeignKey("courts.id"), index=True)
    granted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    granted_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"))

    user: Mapped["User"] = relationship(
        back_populates="court_accesses", foreign_keys=[user_id]
    )
    court: Mapped["Court"] = relationship(back_populates="court_accesses")


class Recording(Base):
    __tablename__ = "recordings"

    id: Mapped[int] = mapped_column(primary_key=True)
    court_id: Mapped[int] = mapped_column(ForeignKey("courts.id"), index=True)
    device_id: Mapped[int] = mapped_column(ForeignKey("devices.id"), index=True)
    camera_index: Mapped[int] = mapped_column(Integer)
    file_key: Mapped[str] = mapped_column(String(512), unique=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, default=30)
    triggered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    court: Mapped["Court"] = relationship(back_populates="recordings")
    device: Mapped["Device"] = relationship(back_populates="recordings")


class CaptureTriggerStatus(str, enum.Enum):
    pending = "pending"
    claimed = "claimed"
    completed = "completed"
    expired = "expired"


class CaptureTrigger(Base):
    """Remote capture request from the mobile app, consumed by the court agent."""

    __tablename__ = "capture_triggers"

    id: Mapped[int] = mapped_column(primary_key=True)
    court_id: Mapped[int] = mapped_column(ForeignKey("courts.id"), index=True)
    camera_index: Mapped[int] = mapped_column(Integer)
    requested_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[CaptureTriggerStatus] = mapped_column(
        Enum(CaptureTriggerStatus),
        default=CaptureTriggerStatus.pending,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    claimed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class PlatformSettings(Base):
    __tablename__ = "platform_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    platform_name: Mapped[str] = mapped_column(String(255), default="Lance On")
    support_email: Mapped[str] = mapped_column(
        String(255), default="suporte@lanceon.com.br"
    )
    timezone: Mapped[str] = mapped_column(String(64), default="America/Sao_Paulo")
    language: Mapped[str] = mapped_column(String(16), default="pt-BR")
    storage_limit_tb: Mapped[float] = mapped_column(default=5.0)
    retention_hours: Mapped[int] = mapped_column(default=48)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class FeedbackReport(Base):
    __tablename__ = "feedback_reports"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    message: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(16), default="new", index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )

    user: Mapped["User"] = relationship()
    images: Mapped[list["FeedbackImage"]] = relationship(
        back_populates="report",
        cascade="all, delete-orphan",
    )


class FeedbackImage(Base):
    __tablename__ = "feedback_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("feedback_reports.id"), index=True)
    file_key: Mapped[str] = mapped_column(String(512))
    content_type: Mapped[str] = mapped_column(String(128), default="image/jpeg")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    report: Mapped["FeedbackReport"] = relationship(back_populates="images")
