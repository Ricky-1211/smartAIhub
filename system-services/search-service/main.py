"""
Search & Global Indexing Service
"""
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import sys
import os
from datetime import datetime
from sqlalchemy import create_engine, Column, String, DateTime, Text, Integer, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.dialects.postgresql import JSONB
import re

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from shared.config import (
    ALLOWED_ORIGINS, POSTGRES_HOST, POSTGRES_PORT,
    POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
)
from shared.utils import create_response, log_error

app = FastAPI(title="Search Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database setup
DATABASE_URL = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}_search"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class SearchIndex(Base):
    __tablename__ = "search_index"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String, index=True)  # log, prediction, user, report
    entity_id = Column(String, index=True)
    title = Column(String)
    content = Column(Text)
    metadata = Column(JSONB)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_entity', 'entity_type', 'entity_id'),
    )


class IndexRequest(BaseModel):
    entity_type: str
    entity_id: str
    title: str
    content: str
    metadata: Optional[Dict] = None


class SearchRequest(BaseModel):
    query: str
    entity_types: Optional[List[str]] = None
    limit: int = 20


class SearchResult(BaseModel):
    entity_type: str
    entity_id: str
    title: str
    content: str
    score: float
    metadata: Dict


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def calculate_relevance_score(query: str, title: str, content: str) -> float:
    """Calculate relevance score"""
    query_lower = query.lower()
    title_lower = title.lower()
    content_lower = content.lower()
    
    score = 0.0
    
    # Title matches (higher weight)
    title_matches = title_lower.count(query_lower)
    score += title_matches * 10
    
    # Content matches
    content_matches = content_lower.count(query_lower)
    score += content_matches * 1
    
    # Word matches
    query_words = query_lower.split()
    for word in query_words:
        if word in title_lower:
            score += 5
        if word in content_lower:
            score += 1
    
    return score


@app.on_event("startup")
async def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/health")
async def health_check():
    return create_response(True, "Search service is healthy")


@app.post("/index")
async def index_document(request: IndexRequest, db: Session = Depends(get_db)):
    """Index a document for search"""
    try:
        # Check if exists
        existing = db.query(SearchIndex).filter(
            SearchIndex.entity_type == request.entity_type,
            SearchIndex.entity_id == request.entity_id
        ).first()
        
        if existing:
            # Update
            existing.title = request.title
            existing.content = request.content
            existing.metadata = request.metadata or {}
            existing.updated_at = datetime.utcnow()
        else:
            # Create
            index_entry = SearchIndex(
                entity_type=request.entity_type,
                entity_id=request.entity_id,
                title=request.title,
                content=request.content,
                metadata=request.metadata or {}
            )
            db.add(index_entry)
        
        db.commit()
        return create_response(True, "Document indexed")
    except Exception as e:
        log_error("search-service", e)
        raise HTTPException(status_code=500, detail="Indexing failed")


@app.post("/search")
async def search(request: SearchRequest, db: Session = Depends(get_db)):
    """Search across indexed documents"""
    try:
        query_obj = db.query(SearchIndex)
        
        if request.entity_types:
            query_obj = query_obj.filter(SearchIndex.entity_type.in_(request.entity_types))
        
        # Simple text search (in production, use full-text search)
        all_docs = query_obj.all()
        
        results = []
        for doc in all_docs:
            score = calculate_relevance_score(
                request.query,
                doc.title or "",
                doc.content or ""
            )
            
            if score > 0:
                results.append({
                    "entity_type": doc.entity_type,
                    "entity_id": doc.entity_id,
                    "title": doc.title,
                    "content": doc.content[:200] + "..." if len(doc.content) > 200 else doc.content,
                    "score": score,
                    "metadata": doc.metadata or {}
                })
        
        # Sort by score
        results.sort(key=lambda x: x["score"], reverse=True)
        results = results[:request.limit]
        
        return create_response(True, "Search completed", results)
    except Exception as e:
        log_error("search-service", e)
        raise HTTPException(status_code=500, detail="Search failed")


@app.get("/search")
async def search_get(
    q: str,
    entity_types: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Search (GET endpoint)"""
    entity_types_list = entity_types.split(',') if entity_types else None
    request = SearchRequest(query=q, entity_types=entity_types_list, limit=limit)
    return await search(request, db)


@app.delete("/index/{entity_type}/{entity_id}")
async def delete_index(
    entity_type: str,
    entity_id: str,
    db: Session = Depends(get_db)
):
    """Delete indexed document"""
    try:
        doc = db.query(SearchIndex).filter(
            SearchIndex.entity_type == entity_type,
            SearchIndex.entity_id == entity_id
        ).first()
        
        if doc:
            db.delete(doc)
            db.commit()
            return create_response(True, "Document removed from index")
        else:
            raise HTTPException(status_code=404, detail="Document not found")
    except HTTPException:
        raise
    except Exception as e:
        log_error("search-service", e)
        raise HTTPException(status_code=500, detail="Deletion failed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8010)

