"""
Shared utility functions
"""
import logging
import json
from typing import Any, Dict, Optional
from datetime import datetime
import hashlib

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def create_response(
    success: bool,
    message: str,
    data: Any = None,
    status_code: int = 200
) -> Dict[str, Any]:
    """Create standardized API response"""
    response = {
        "success": success,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }
    if data is not None:
        response["data"] = data
    return response


def hash_string(text: str) -> str:
    """Hash a string using SHA256"""
    return hashlib.sha256(text.encode()).hexdigest()


def validate_email(email: str) -> bool:
    """Basic email validation"""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def log_request(service_name: str, endpoint: str, method: str, user_id: Optional[str] = None):
    """Log API request"""
    logger.info(f"[{service_name}] {method} {endpoint} - User: {user_id or 'Anonymous'}")


def log_error(service_name: str, error: Exception, context: Optional[Dict] = None):
    """Log error with context"""
    error_msg = {
        "service": service_name,
        "error": str(error),
        "type": type(error).__name__,
        "context": context or {}
    }
    logger.error(json.dumps(error_msg, indent=2))


def sanitize_input(text: str) -> str:
    """Basic input sanitization"""
    if not isinstance(text, str):
        return ""
    return text.strip()


def format_timestamp(dt: datetime) -> str:
    """Format datetime to ISO string"""
    return dt.isoformat()

