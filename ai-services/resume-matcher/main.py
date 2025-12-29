"""
Resume & Job Matching Service
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import sys
import os
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from shared.config import ALLOWED_ORIGINS
from shared.utils import create_response, log_error

app = FastAPI(title="Resume Matcher Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Common skills keywords
TECH_SKILLS = [
    "python", "java", "javascript", "react", "node", "sql", "mongodb",
    "postgresql", "docker", "kubernetes", "aws", "azure", "git", "linux",
    "machine learning", "deep learning", "tensorflow", "pytorch", "nlp",
    "data science", "analytics", "api", "rest", "graphql", "microservices"
]


class JobDescription(BaseModel):
    title: str
    description: str
    required_skills: List[str]
    experience_years: Optional[int] = None


class ResumeMatchRequest(BaseModel):
    resume_text: str
    job_description: JobDescription


class MatchResult(BaseModel):
    match_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    recommendations: List[str]
    job_title: str


def extract_skills(text: str) -> List[str]:
    """Extract skills from text"""
    text_lower = text.lower()
    found_skills = []
    
    for skill in TECH_SKILLS:
        if skill in text_lower:
            found_skills.append(skill)
    
    # Also look for common patterns
    skill_patterns = [
        r'\b\d+\+?\s*years?\s*(?:of\s*)?experience\b',
        r'\b(?:proficient|experienced|skilled)\s+in\s+([^,\.]+)',
    ]
    
    return list(set(found_skills))


def calculate_match_score(resume_text: str, job_description: JobDescription) -> Dict:
    """Calculate match score between resume and job description"""
    # Extract skills from resume
    resume_skills = extract_skills(resume_text)
    
    # Combine job description text
    job_text = f"{job_description.title} {job_description.description} " + \
               " ".join(job_description.required_skills)
    job_skills = extract_skills(job_text)
    
    # Calculate similarity using TF-IDF
    vectorizer = TfidfVectorizer(stop_words='english')
    texts = [resume_text.lower(), job_text.lower()]
    tfidf_matrix = vectorizer.fit_transform(texts)
    similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    
    # Skill-based matching
    matched_skills = [skill for skill in job_description.required_skills 
                     if skill.lower() in resume_text.lower()]
    missing_skills = [skill for skill in job_description.required_skills 
                     if skill.lower() not in resume_text.lower()]
    
    # Calculate skill match percentage
    if job_description.required_skills:
        skill_match_ratio = len(matched_skills) / len(job_description.required_skills)
    else:
        skill_match_ratio = 0.0
    
    # Combined score (weighted)
    final_score = (similarity * 0.6 + skill_match_ratio * 0.4) * 100
    
    # Generate recommendations
    recommendations = []
    if missing_skills:
        recommendations.append(f"Consider highlighting: {', '.join(missing_skills[:3])}")
    if similarity < 0.5:
        recommendations.append("Resume content doesn't align well with job description")
    if len(resume_skills) < 5:
        recommendations.append("Add more technical skills to your resume")
    
    return {
        "match_score": round(final_score, 2),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "recommendations": recommendations,
        "similarity_score": round(float(similarity) * 100, 2),
        "skill_match_ratio": round(skill_match_ratio * 100, 2)
    }


@app.get("/health")
async def health_check():
    return create_response(True, "Resume matcher service is healthy")


@app.post("/match")
async def match_resume(request: ResumeMatchRequest):
    """Match resume with job description"""
    try:
        result = calculate_match_score(request.resume_text, request.job_description)
        
        return create_response(
            True,
            "Resume matching completed",
            {
                "match_score": result["match_score"],
                "matched_skills": result["matched_skills"],
                "missing_skills": result["missing_skills"],
                "recommendations": result["recommendations"],
                "job_title": request.job_description.title,
                "details": {
                    "similarity_score": result["similarity_score"],
                    "skill_match_ratio": result["skill_match_ratio"]
                }
            }
        )
    except Exception as e:
        log_error("resume-service", e)
        raise HTTPException(status_code=500, detail="Matching failed")


@app.post("/extract-skills")
async def extract_resume_skills(resume_text: str):
    """Extract skills from resume text"""
    try:
        skills = extract_skills(resume_text)
        return create_response(True, "Skills extracted", {"skills": skills})
    except Exception as e:
        log_error("resume-service", e)
        raise HTTPException(status_code=500, detail="Skill extraction failed")


@app.post("/match-file")
async def match_resume_file(
    resume_file: UploadFile = File(...),
    job_title: str = "",
    job_description: str = "",
    required_skills: str = ""
):
    """Match resume from uploaded file"""
    try:
        content = await resume_file.read()
        resume_text = content.decode('utf-8', errors='ignore')
        
        # Parse required skills
        skills_list = [s.strip() for s in required_skills.split(',') if s.strip()]
        
        job_desc = JobDescription(
            title=job_title,
            description=job_description,
            required_skills=skills_list
        )
        
        request = ResumeMatchRequest(
            resume_text=resume_text,
            job_description=job_desc
        )
        
        return await match_resume(request)
    except Exception as e:
        log_error("resume-service", e)
        raise HTTPException(status_code=500, detail="File matching failed")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8005)

