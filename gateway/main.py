"""
API Gateway - Routes requests to appropriate microservices
"""
from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import sys
import os
import asyncio
from datetime import datetime

# Add shared to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from shared.config import (
    AUTH_SERVICE_URL, SPAM_SERVICE_URL, WHATSAPP_SERVICE_URL,
    MOVIE_SERVICE_URL, RESUME_SERVICE_URL, HOUSE_SERVICE_URL,
    FRAUD_SERVICE_URL, CODE_REVIEW_SERVICE_URL, LOGGING_SERVICE_URL,
    SEARCH_SERVICE_URL, MODEL_MGMT_SERVICE_URL, ALLOWED_ORIGINS
)
from shared.utils import log_request, log_error, create_response

app = FastAPI(title="SmartAIHub API Gateway", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service routing map
SERVICE_ROUTES = {
    "/auth": AUTH_SERVICE_URL,
    "/spam": SPAM_SERVICE_URL,
    "/whatsapp": WHATSAPP_SERVICE_URL,
    "/movie": MOVIE_SERVICE_URL,
    "/resume": RESUME_SERVICE_URL,
    "/house": HOUSE_SERVICE_URL,
    "/fraud": FRAUD_SERVICE_URL,
    "/code-review": CODE_REVIEW_SERVICE_URL,
    "/logging": LOGGING_SERVICE_URL,
    "/search": SEARCH_SERVICE_URL,
    "/models": MODEL_MGMT_SERVICE_URL,
}

# Reverse lookup: service URL -> service name
SERVICE_NAMES = {
    AUTH_SERVICE_URL: "auth-service",
    SPAM_SERVICE_URL: "spam-service",
    WHATSAPP_SERVICE_URL: "whatsapp-service",
    MOVIE_SERVICE_URL: "movie-service",
    RESUME_SERVICE_URL: "resume-service",
    HOUSE_SERVICE_URL: "house-service",
    FRAUD_SERVICE_URL: "fraud-service",
    CODE_REVIEW_SERVICE_URL: "code-review-service",
    LOGGING_SERVICE_URL: "logging-service",
    SEARCH_SERVICE_URL: "search-service",
    MODEL_MGMT_SERVICE_URL: "model-mgmt-service",
}


async def forward_request(
    service_url: str,
    path: str,
    method: str,
    headers: dict,
    body: dict = None,
    params: dict = None,
    is_form_data: bool = False,
    content_type: str = ""
):
    """Forward request to microservice"""
    service_name = SERVICE_NAMES.get(service_url, "unknown-service")
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{service_url}{path}"
            
            # Prepare headers (remove host, content-length, etc.)
            forward_headers = {
                k: v for k, v in headers.items()
                if k.lower() not in ['host', 'content-length', 'connection']
            }
            
            if method == "GET":
                response = await client.get(url, headers=forward_headers, params=params)
            elif method == "POST":
                if is_form_data:
                    # Send raw body with original content-type for form data
                    # Preserve the content-type header for multipart boundaries
                    if "content-type" not in forward_headers:
                        forward_headers["content-type"] = content_type
                    response = await client.post(url, headers=forward_headers, content=body, params=params)
                else:
                    # Send as JSON
                    response = await client.post(url, headers=forward_headers, json=body, params=params)
            elif method == "PUT":
                if is_form_data:
                    # Send raw body with original content-type for form data
                    if "content-type" not in forward_headers:
                        forward_headers["content-type"] = content_type
                    response = await client.put(url, headers=forward_headers, content=body, params=params)
                else:
                    response = await client.put(url, headers=forward_headers, json=body, params=params)
            elif method == "DELETE":
                response = await client.delete(url, headers=forward_headers, params=params)
            else:
                raise HTTPException(status_code=405, detail="Method not allowed")
            
            # Get response content
            content_type = response.headers.get("content-type", "")
            if content_type.startswith("application/json"):
                try:
                    content = response.json()
                except:
                    content = {"data": response.text}
            else:
                content = {"data": response.text}
            
            # Prepare response headers (exclude headers that shouldn't be forwarded)
            response_headers = {
                k: v for k, v in response.headers.items()
                if k.lower() not in [
                    'content-length',  # Let FastAPI calculate this
                    'content-encoding',  # May differ
                    'transfer-encoding',  # Not needed
                    'connection',  # Connection-specific
                    'server',  # Gateway is the server
                    'date'  # Let FastAPI set current date
                ]
            }
            
            return JSONResponse(
                content=content,
                status_code=response.status_code,
                headers=response_headers
            )
    except httpx.TimeoutException:
        error_msg = f"{service_name} timeout - service did not respond within 30 seconds"
        log_error("gateway", Exception(error_msg), {"path": path, "service_url": service_url, "service_name": service_name})
        raise HTTPException(status_code=504, detail=error_msg)
    except httpx.ConnectError as e:
        error_msg = f"{service_name} unavailable - cannot connect to {service_url}. Ensure the service is running."
        log_error("gateway", e, {"path": path, "service_url": service_url, "service_name": service_name})
        raise HTTPException(status_code=503, detail=error_msg)
    except Exception as e:
        error_msg = f"Internal gateway error while connecting to {service_name}"
        log_error("gateway", e, {"path": path, "service_url": service_url, "service_name": service_name})
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/health")
async def health_check():
    """Gateway health check"""
    return create_response(True, "API Gateway is healthy")


@app.get("/services/status")
async def services_status():
    """Check status of all microservices"""
    status = {}
    
    async def check_service(name: str, url: str):
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{url}/health")
                status[name] = {
                    "status": "healthy",
                    "url": url,
                    "response_time": response.elapsed.total_seconds() if hasattr(response, 'elapsed') else None
                }
        except httpx.TimeoutException:
            status[name] = {
                "status": "timeout",
                "url": url,
                "error": "Service did not respond within 5 seconds"
            }
        except httpx.ConnectError:
            status[name] = {
                "status": "unavailable",
                "url": url,
                "error": "Cannot connect to service - service may not be running"
            }
        except Exception as e:
            status[name] = {
                "status": "error",
                "url": url,
                "error": str(e)
            }
    
    # Check all services in parallel
    tasks = [check_service(name, url) for name, url in SERVICE_NAMES.items()]
    await asyncio.gather(*tasks)
    
    return {
        "gateway": "healthy",
        "services": status,
        "timestamp": datetime.now().isoformat()
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "SmartAIHub API Gateway",
        "version": "1.0.0",
        "services": list(SERVICE_ROUTES.keys())
    }


@app.api_route("/{service_path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def gateway_router(request: Request, service_path: str):
    """Route requests to appropriate microservice"""
    # Determine which service to route to
    service_url = None
    remaining_path = service_path
    
    for route_prefix, url in SERVICE_ROUTES.items():
        prefix_clean = route_prefix.lstrip("/")
        if service_path.startswith(prefix_clean):
            service_url = url
            # Remove the prefix from the path, ensuring we don't create double slashes
            remaining_path = service_path[len(prefix_clean):].lstrip("/")
            break
    
    if not service_url:
        raise HTTPException(status_code=404, detail="Service not found")
    
    # Get request body and content type
    body = None
    content_type = request.headers.get("content-type", "")
    is_form_data = "application/x-www-form-urlencoded" in content_type or "multipart/form-data" in content_type
    
    if request.method in ["POST", "PUT", "PATCH"]:
        if is_form_data:
            # For form data, read raw body to preserve multipart boundaries
            body_bytes = await request.body()
            body = body_bytes
        else:
            # For JSON, read as JSON
            try:
                body = await request.json()
            except:
                pass
    
    # Get query parameters
    params = dict(request.query_params)
    
    # Forward request - ensure path starts with / and doesn't have double slashes
    forward_path = f"/{remaining_path}" if remaining_path else "/"
    log_request("gateway", f"/{service_path}", request.method)
    return await forward_request(
        service_url,
        forward_path,
        request.method,
        dict(request.headers),
        body,
        params,
        is_form_data,
        content_type
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

