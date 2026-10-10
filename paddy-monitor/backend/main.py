import os
from datetime import timedelta
from typing import Optional

from fastapi import FastAPI, Depends, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
from database import Base, engine, get_db
from quality import classify, build_alerts

Base.metadata.create_all(bind=engine)

# Devices send this key in the "X-API-Key" header. Set a real one in production.
API_KEY = os.getenv("DEVICE_API_KEY", "change-me")

app = FastAPI(title="Paddy Moisture Monitoring API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------- schemas ----------
class DeviceIn(BaseModel):
    name: str = Field(min_length=1)
    location: str = ""


class ReadingIn(BaseModel):
    device: str
    moisture: float = Field(ge=0, le=100)
    temperature: float = Field(ge=-20, le=80)
    humidity: float = Field(ge=0, le=100)


def check_key(x_api_key: Optional[str] = Header(default=None)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing X-API-Key")


def reading_dict(r: models.Reading):
    return {
        "id": r.id, "device_id": r.device_id, "moisture": r.moisture,
        "temperature": r.temperature, "humidity": r.humidity,
        "status": r.status, "created_at": r.created_at.isoformat(),
    }


# ---------- devices ----------
@app.post("/devices", status_code=201, dependencies=[Depends(check_key)])
def create_device(body: DeviceIn, db: Session = Depends(get_db)):
    if db.query(models.Device).filter_by(name=body.name).first():
        raise HTTPException(409, "Device name already exists")
    d = models.Device(name=body.name, location=body.location)
    db.add(d)
    db.commit()
    db.refresh(d)
    return {"id": d.id, "name": d.name, "location": d.location}


@app.get("/devices")
def list_devices(db: Session = Depends(get_db)):
    return [{"id": d.id, "name": d.name, "location": d.location} for d in db.query(models.Device)]


# ---------- readings ----------
@app.post("/readings", status_code=201, dependencies=[Depends(check_key)])
def add_reading(body: ReadingIn, db: Session = Depends(get_db)):
    device = db.query(models.Device).filter_by(name=body.device).first()
    if not device:
        raise HTTPException(404, f"Unknown device '{body.device}'. Create it first with POST /devices")

    status = classify(body.moisture)
    r = models.Reading(device_id=device.id, moisture=body.moisture,
                       temperature=body.temperature, humidity=body.humidity, status=status)
    db.add(r)
    db.flush()  # gives r an id before we create alerts

    for severity, message in build_alerts(body.moisture, body.temperature, body.humidity):
        db.add(models.Alert(device_id=device.id, reading_id=r.id, message=message, severity=severity))
    db.commit()
    db.refresh(r)
    return reading_dict(r)


@app.get("/readings")
def list_readings(device_id: Optional[int] = None, hours: int = Query(24, ge=1, le=720),
                  limit: int = Query(500, ge=1, le=5000), db: Session = Depends(get_db)):
    q = db.query(models.Reading)
    if device_id:
        q = q.filter(models.Reading.device_id == device_id)
    latest = db.query(func.max(models.Reading.created_at)).scalar()
    if latest:  # window is relative to the newest reading so old demo data still shows
        q = q.filter(models.Reading.created_at >= latest - timedelta(hours=hours))
    rows = q.order_by(models.Reading.created_at.desc()).limit(limit).all()
    return [reading_dict(r) for r in reversed(rows)]


@app.get("/summary")
def summary(db: Session = Depends(get_db)):
    """Latest reading per device plus counts of each status."""
    out = []
    for d in db.query(models.Device):
        r = (db.query(models.Reading).filter_by(device_id=d.id)
             .order_by(models.Reading.created_at.desc()).first())
        open_alerts = db.query(models.Alert).filter_by(device_id=d.id, acknowledged=False).count()
        out.append({"device": d.name, "location": d.location,
                    "latest": reading_dict(r) if r else None, "open_alerts": open_alerts})
    return out


# ---------- alerts ----------
@app.get("/alerts")
def list_alerts(only_open: bool = True, db: Session = Depends(get_db)):
    q = db.query(models.Alert)
    if only_open:
        q = q.filter_by(acknowledged=False)
    return [{"id": a.id, "device_id": a.device_id, "message": a.message, "severity": a.severity,
             "acknowledged": a.acknowledged, "created_at": a.created_at.isoformat()}
            for a in q.order_by(models.Alert.created_at.desc()).limit(100)]


@app.post("/alerts/{alert_id}/ack", dependencies=[Depends(check_key)])
def ack_alert(alert_id: int, db: Session = Depends(get_db)):
    a = db.get(models.Alert, alert_id)
    if not a:
        raise HTTPException(404, "Alert not found")
    a.acknowledged = True
    db.commit()
    return {"id": a.id, "acknowledged": True}
