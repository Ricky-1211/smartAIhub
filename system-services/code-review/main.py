"""
Code Review Automation Service
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Optional
import sys
import os
import re
import ast
import subprocess
import tempfile

sys.path.append(os.path.join(os.path.dirname(__file__), '../..'))

from shared.config import ALLOWED_ORIGINS
from shared.utils import create_response, log_error

app = FastAPI(title="Code Review Service", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CodeReviewRequest(BaseModel):
    code: str
    language: str = "python"  # python, javascript, etc.


class CodeIssue(BaseModel):
    type: str  # security, style, quality, performance
    severity: str  # high, medium, low
    line: int
    message: str
    suggestion: Optional[str] = None


class CodeReviewResponse(BaseModel):
    score: float  # 0-100
    issues: List[CodeIssue]
    metrics: Dict
    suggestions: List[str]


# Security patterns
SECURITY_PATTERNS = {
    "sql_injection": [
        r"execute\s*\(\s*['\"].*%.*['\"]",
        r"query\s*\(\s*['\"].*\+.*['\"]",
    ],
    "hardcoded_secrets": [
        r"(?:password|secret|api_key|token)\s*=\s*['\"][^'\"]+['\"]",
        r"api[_-]?key\s*[:=]\s*['\"][^'\"]+['\"]",
    ],
    "eval_usage": [
        r"eval\s*\(",
        r"exec\s*\(",
    ],
    "unsafe_deserialization": [
        r"pickle\.loads\s*\(",
        r"yaml\.load\s*\(",
    ],
}


def check_security(code: str, language: str) -> List[CodeIssue]:
    """Check for security issues"""
    issues = []
    lines = code.split('\n')
    
    for pattern_name, patterns in SECURITY_PATTERNS.items():
        for pattern in patterns:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(CodeIssue(
                        type="security",
                        severity="high",
                        line=i,
                        message=f"Potential {pattern_name.replace('_', ' ')} detected",
                        suggestion=f"Review line {i} for security vulnerabilities"
                    ))
    
    return issues


def check_code_quality(code: str, language: str) -> List[CodeIssue]:
    """Check code quality issues"""
    issues = []
    lines = code.split('\n')
    
    # Check for long lines
    for i, line in enumerate(lines, 1):
        if len(line) > 120:
            issues.append(CodeIssue(
                type="style",
                severity="low",
                line=i,
                message=f"Line {i} exceeds 120 characters",
                suggestion="Break long lines for better readability"
            ))
    
    # Check for TODO/FIXME comments
    for i, line in enumerate(lines, 1):
        if re.search(r'(TODO|FIXME|XXX|HACK)', line, re.IGNORECASE):
            issues.append(CodeIssue(
                type="quality",
                severity="medium",
                line=i,
                message=f"TODO/FIXME comment found",
                suggestion="Address the TODO/FIXME before merging"
            ))
    
    # Check for print statements (in production code)
    for i, line in enumerate(lines, 1):
        if re.search(r'^\s*print\s*\(', line):
            issues.append(CodeIssue(
                type="quality",
                severity="low",
                line=i,
                message="Print statement found",
                suggestion="Use proper logging instead of print statements"
            ))
    
    return issues


def check_python_syntax(code: str) -> List[CodeIssue]:
    """Check Python syntax"""
    issues = []
    try:
        ast.parse(code)
    except SyntaxError as e:
        issues.append(CodeIssue(
            type="quality",
            severity="high",
            line=e.lineno or 0,
            message=f"Syntax error: {e.msg}",
            suggestion="Fix syntax error before proceeding"
        ))
    return issues


def calculate_metrics(code: str) -> Dict:
    """Calculate code metrics"""
    lines = code.split('\n')
    total_lines = len(lines)
    code_lines = len([l for l in lines if l.strip() and not l.strip().startswith('#')])
    comment_lines = len([l for l in lines if l.strip().startswith('#')])
    blank_lines = total_lines - code_lines - comment_lines
    
    # Count functions/classes (basic)
    function_count = len(re.findall(r'^\s*def\s+\w+', code, re.MULTILINE))
    class_count = len(re.findall(r'^\s*class\s+\w+', code, re.MULTILINE))
    
    return {
        "total_lines": total_lines,
        "code_lines": code_lines,
        "comment_lines": comment_lines,
        "blank_lines": blank_lines,
        "functions": function_count,
        "classes": class_count,
        "comment_ratio": round(comment_lines / code_lines * 100, 2) if code_lines > 0 else 0
    }


def review_code(code: str, language: str) -> CodeReviewResponse:
    """Perform code review"""
    issues = []
    
    # Security checks
    issues.extend(check_security(code, language))
    
    # Quality checks
    issues.extend(check_code_quality(code, language))
    
    # Syntax checks (for Python)
    if language.lower() == "python":
        issues.extend(check_python_syntax(code))
    
    # Calculate metrics
    metrics = calculate_metrics(code)
    
    # Calculate score (0-100)
    base_score = 100
    for issue in issues:
        if issue.severity == "high":
            base_score -= 10
        elif issue.severity == "medium":
            base_score -= 5
        else:
            base_score -= 2
    
    score = max(0, min(100, base_score))
    
    # Generate suggestions
    suggestions = []
    if metrics.get("comment_ratio", 0) < 10:
        suggestions.append("Add more comments to improve code documentation")
    if len(issues) > 10:
        suggestions.append("Consider refactoring to reduce code complexity")
    if score < 70:
        suggestions.append("Address high and medium severity issues before merging")
    
    return CodeReviewResponse(
        score=round(score, 2),
        issues=issues,
        metrics=metrics,
        suggestions=suggestions
    )


@app.get("/health")
async def health_check():
    return create_response(True, "Code review service is healthy")


@app.post("/review", response_model=CodeReviewResponse)
async def review_code_endpoint(request: CodeReviewRequest):
    """Review code"""
    try:
        result = review_code(request.code, request.language)
        return result
    except Exception as e:
        log_error("code-review-service", e)
        raise HTTPException(status_code=500, detail="Code review failed")


@app.post("/review-file")
async def review_code_file(code: str, language: str = "python"):
    """Review code from file content"""
    request = CodeReviewRequest(code=code, language=language)
    return await review_code_endpoint(request)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8008)

