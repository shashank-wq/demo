from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey, Boolean
from database import Base


def now():
    return datetime.now(timezone.utc)


class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)   # e.g. "godown-1"
    location = Column(String, default="")


class Reading(Base):
    __tablename__ = "readings"
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"), index=True)
    moisture = Column(Float, nullable=False)      # % grain moisture
    temperature = Column(Float, nullable=False)   # deg C
    humidity = Column(Float, nullable=False)      # % relative humidity
    status = Column(String, nullable=False)       # dry / optimal / excess
    created_at = Column(DateTime(timezone=True), default=now, index=True)


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(Integer, primary_key=True)
    device_id = Column(Integer, ForeignKey("devices.id"), index=True)
    reading_id = Column(Integer, ForeignKey("readings.id"))
    message = Column(String, nullable=False)
    severity = Column(String, nullable=False)     # warning / critical
    acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=now)
