from fastapi import APIRouter
from pydantic import BaseModel

# Create a router for this endpoint
router = APIRouter()

class HealthCheckResponse(BaseModel):
    """
    Pydantic model for the health check response.
    """
    status: str
    message: str

@router.get("/", response_model=HealthCheckResponse)
async def health_check():
    """
    Health Check Endpoint.
    
    Returns the operational status of the API.
    This is useful for monitoring and load balancers.
    """
    return {"status": "ok", "message": "API is running smoothly"}
