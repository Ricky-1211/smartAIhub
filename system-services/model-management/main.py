"""
Model Management System (MLOps)
"""
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import sys
import os
import json
import pickle
from datetime import datetime
from sqlalchemy import create_engine, Column, String, DateTime, Float, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from shared.config import (
    ALLOWED_ORIGINS, POSTGRES_HOST, POSTGRES_PORT,
    POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
)
from shared.utils import create_response, log_error

app = FastAPI(title="Model Management Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Model storage
MODELS_DIR = "models"
os.makedirs(MODELS_DIR, exist_ok=True)

# Database setup
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}_models"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Model(Base):
    __tablename__ = "models"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, index=True)
    version = Column(String, index=True)
    service_name = Column(String, index=True)
    file_path = Column(String)
    accuracy = Column(Float, nullable=True)
    is_active = Column(Boolean, default=False)
    metadata = Column(String)  # JSON string
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String)


class ModelUploadRequest(BaseModel):
    name: str
    version: str
    service_name: str
    accuracy: Optional[float] = None
    metadata: Optional[Dict] = None
    created_by: str


class ModelResponse(BaseModel):
    id: int
    name: str
    version: str
    service_name: str
    file_path: str
    accuracy: Optional[float]
    is_active: bool
    metadata: Dict
    created_at: str
    created_by: str


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
    return create_response(True, "Model management service is healthy")


@app.post("/upload")
async def upload_model(
    request: ModelUploadRequest,
    model_file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a new model version"""
    try:
        # Check if model with same name and version exists
        existing = db.query(Model).filter(
            Model.name == request.name,
            Model.version == request.version
        ).first()
        
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Model {request.name} version {request.version} already exists"
            )
        
        # Save file
        file_path = os.path.join(
            MODELS_DIR,
            f"{request.service_name}_{request.name}_v{request.version}.pkl"
        )
        
        with open(file_path, "wb") as f:
            content = await model_file.read()
            f.write(content)
        
        # Create database entry
        model = Model(
            name=request.name,
            version=request.version,
            service_name=request.service_name,
            file_path=file_path,
            accuracy=request.accuracy,
            metadata=json.dumps(request.metadata or {}),
            created_by=request.created_by
        )
        
        db.add(model)
        db.commit()
        db.refresh(model)
        
        return create_response(
            True,
            "Model uploaded successfully",
            {
                "id": model.id,
                "name": model.name,
                "version": model.version
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        log_error("model-mgmt-service", e)
        raise HTTPException(status_code=500, detail="Model upload failed")


@app.get("/models")
async def list_models(
    service_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all models"""
    try:
        query = db.query(Model)
        if service_name:
            query = query.filter(Model.service_name == service_name)
        
        models = query.order_by(Model.created_at.desc()).all()
        
        results = [{
            "id": m.id,
            "name": m.name,
            "version": m.version,
            "service_name": m.service_name,
            "file_path": m.file_path,
            "accuracy": m.accuracy,
            "is_active": m.is_active,
            "metadata": json.loads(m.metadata) if m.metadata else {},
            "created_at": m.created_at.isoformat(),
            "created_by": m.created_by
        } for m in models]
        
        return create_response(True, "Models retrieved", results)
    except Exception as e:
        log_error("model-mgmt-service", e)
        raise HTTPException(status_code=500, detail="Failed to list models")


@app.get("/models/{model_id}")
async def get_model(model_id: int, db: Session = Depends(get_db)):
    """Get model details"""
    try:
        model = db.query(Model).filter(Model.id == model_id).first()
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        return create_response(True, "Model retrieved", {
            "id": model.id,
            "name": model.name,
            "version": model.version,
            "service_name": model.service_name,
            "file_path": model.file_path,
            "accuracy": model.accuracy,
            "is_active": model.is_active,
            "metadata": json.loads(model.metadata) if model.metadata else {},
            "created_at": model.created_at.isoformat(),
            "created_by": model.created_by
        })
    except HTTPException:
        raise
    except Exception as e:
        log_error("model-mgmt-service", e)
        raise HTTPException(status_code=500, detail="Failed to get model")


@app.post("/models/{model_id}/activate")
async def activate_model(model_id: int, db: Session = Depends(get_db)):
    """Activate a model version"""
    try:
        model = db.query(Model).filter(Model.id == model_id).first()
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Deactivate other versions of the same model
        db.query(Model).filter(
            Model.name == model.name,
            Model.service_name == model.service_name
        ).update({"is_active": False})
        
        # Activate this model
        model.is_active = True
        db.commit()
        
        return create_response(True, "Model activated")
    except HTTPException:
        raise
    except Exception as e:
        log_error("model-mgmt-service", e)
        raise HTTPException(status_code=500, detail="Failed to activate model")


@app.delete("/models/{model_id}")
async def delete_model(model_id: int, db: Session = Depends(get_db)):
    """Delete a model"""
    try:
        model = db.query(Model).filter(Model.id == model_id).first()
        if not model:
            raise HTTPException(status_code=404, detail="Model not found")
        
        # Delete file
        if os.path.exists(model.file_path):
            os.remove(model.file_path)
        
        # Delete from database
        db.delete(model)
        db.commit()
        
        return create_response(True, "Model deleted")
    except HTTPException:
        raise
    except Exception as e:
        log_error("model-mgmt-service", e)
        raise HTTPException(status_code=500, detail="Failed to delete model")


@app.get("/models/{service_name}/active")
async def get_active_model(service_name: str, db: Session = Depends(get_db)):
    """Get active model for a service"""
    try:
        model = db.query(Model).filter(
            Model.service_name == service_name,
            Model.is_active == True
        ).first()
        
        if not model:
            raise HTTPException(
                status_code=404,
                detail=f"No active model found for service {service_name}"
            )
        
        return create_response(True, "Active model retrieved", {
            "id": model.id,
            "name": model.name,
            "version": model.version,
            "file_path": model.file_path,
            "accuracy": model.accuracy,
            "metadata": json.loads(model.metadata) if model.metadata else {}
        })
    except HTTPException:
        raise
    except Exception as e:
        log_error("model-mgmt-service", e)
        raise HTTPException(status_code=500, detail="Failed to get active model")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8011)

