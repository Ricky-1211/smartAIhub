"""
Distributed Logging & Monitoring Service
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import sys
import os
import json
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import JSONB

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from shared.config import (
    ALLOWED_ORIGINS, POSTGRES_HOST, POSTGRES_PORT,
    POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
)
from shared.utils import create_response, log_error

app = FastAPI(title="Logging Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}_logs"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class LogEntry(Base):
    __tablename__ = "logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    service_name = Column(String, index=True)
    level = Column(String, index=True)  # INFO, ERROR, WARNING, DEBUG
    message = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)
    metadata = Column(JSONB)
    user_id = Column(String, index=True, nullable=True)
    request_id = Column(String, index=True, nullable=True)
    
    __table_args__ = (
        Index('idx_service_timestamp', 'service_name', 'timestamp'),
    )


class LogRequest(BaseModel):
    service_name: str
    level: str
    message: str
    metadata: Optional[Dict] = None
    user_id: Optional[str] = None
    request_id: Optional[str] = None


class LogQuery(BaseModel):
    service_name: Optional[str] = None
    level: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    user_id: Optional[str] = None
    limit: int = 100


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
async def health_check():
    return create_response(True, "Logging service is healthy")


@app.post("/log")
async def create_log(log_request: LogRequest, db: Session = Depends(get_db)):
    """Create a log entry"""
    try:
        log_entry = LogEntry(
            service_name=log_request.service_name,
            level=log_request.level.upper(),
            message=log_request.message,
            metadata=log_request.metadata or {},
            user_id=log_request.user_id,
            request_id=log_request.request_id
        )
        db.add(log_entry)
        db.commit()
        db.refresh(log_entry)
        
        return create_response(True, "Log entry created", {"id": log_entry.id})
    except Exception as e:
        log_error("logging-service", e)
        raise HTTPException(status_code=500, detail="Failed to create log entry")


@app.post("/logs/query")
async def query_logs(query: LogQuery, db: Session = Depends(get_db)):
    """Query logs"""
    try:
        query_obj = db.query(LogEntry)
        
        if query.service_name:
            query_obj = query_obj.filter(LogEntry.service_name == query.service_name)
        if query.level:
            query_obj = query_obj.filter(LogEntry.level == query.level.upper())
        if query.user_id:
            query_obj = query_obj.filter(LogEntry.user_id == query.user_id)
        if query.start_time:
            start_dt = datetime.fromisoformat(query.start_time.replace('Z', '+00:00'))
            query_obj = query_obj.filter(LogEntry.timestamp >= start_dt)
        if query.end_time:
            end_dt = datetime.fromisoformat(query.end_time.replace('Z', '+00:00'))
            query_obj = query_obj.filter(LogEntry.timestamp <= end_dt)
        
        logs = query_obj.order_by(LogEntry.timestamp.desc()).limit(query.limit).all()
        
        results = [{
            "id": log.id,
            "service_name": log.service_name,
            "level": log.level,
            "message": log.message,
            "timestamp": log.timestamp.isoformat(),
            "metadata": log.metadata,
            "user_id": log.user_id,
            "request_id": log.request_id
        } for log in logs]
        
        return create_response(True, "Logs retrieved", results)
    except Exception as e:
        log_error("logging-service", e)
        raise HTTPException(status_code=500, detail="Failed to query logs")


@app.get("/logs/stats")
async def get_log_stats(
    service_name: Optional[str] = None,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get log statistics"""
    try:
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = db.query(LogEntry).filter(LogEntry.timestamp >= start_time)
        
        if service_name:
            query = query.filter(LogEntry.service_name == service_name)
        
        logs = query.all()
        
        # Calculate stats
        total_logs = len(logs)
        by_level = {}
        by_service = {}
        
        for log in logs:
            by_level[log.level] = by_level.get(log.level, 0) + 1
            by_service[log.service_name] = by_service.get(log.service_name, 0) + 1
        
        return create_response(True, "Stats retrieved", {
            "total_logs": total_logs,
            "time_range_hours": hours,
            "by_level": by_level,
            "by_service": by_service
        })
    except Exception as e:
        log_error("logging-service", e)
        raise HTTPException(status_code=500, detail="Failed to get stats")


@app.get("/logs/errors")
async def get_errors(
    service_name: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get recent error logs"""
    try:
        query = db.query(LogEntry).filter(LogEntry.level == "ERROR")
        
        if service_name:
            query = query.filter(LogEntry.service_name == service_name)
        
        errors = query.order_by(LogEntry.timestamp.desc()).limit(limit).all()
        
        results = [{
            "id": log.id,
            "service_name": log.service_name,
            "message": log.message,
            "timestamp": log.timestamp.isoformat(),
            "metadata": log.metadata
        } for log in errors]
        
        return create_response(True, "Errors retrieved", results)
    except Exception as e:
        log_error("logging-service", e)
        raise HTTPException(status_code=500, detail="Failed to get errors")


if __name__ == "__main__":
    from fastapi import Depends
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8009)

