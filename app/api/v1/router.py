from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, users, folders, files, bulk, browse


# Master router for the v1 API
api_router = APIRouter()

# Routers from individual endpoint files
api_router.include_router(health.router, prefix="/health", tags=["Health"])
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"]) # auth router
api_router.include_router(users.router, prefix="/users", tags=["Users"]) # users router
api_router.include_router(folders.router, prefix="/folders", tags=["Folders"]) # Folders router
api_router.include_router(files.router, prefix="/files", tags=["Files"]) # Files router
api_router.include_router(bulk.router, prefix="/bulk", tags=["Bulk Operations"]) # Bulk router
api_router.include_router(browse.router, prefix="/browse", tags=["Browse"]) # Browse router

