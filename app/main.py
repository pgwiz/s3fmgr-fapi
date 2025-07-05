from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1.router import api_router

# Create the FastAPI app instance
app = FastAPI(
    title="File Server Management API",
    description="A robust API for managing files, folders, and storage.",
    version="0.1.0",
)

# --- CORS (Cross-Origin Resource Sharing) Middleware ---
# This allows your frontend (if it's on a different domain)
# to communicate with this API.
# Update origins to a more restrictive list in production.
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:8080",
    # Add your frontend domain here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods (GET, POST, etc.)
    allow_headers=["*"], # Allows all headers
)

# Include the main API router
# All routes defined in api_router will be prefixed with /api/v1
app.include_router(api_router, prefix="/api/v1")

@app.get("/", tags=["Root"])
async def read_root():
    """
    A simple root endpoint to confirm the API is running.
    """
    return {"message": "Welcome to the File Server API!"}




# --- To run this application ---
# 1. Make sure you have the directory structure from the plan.
# 2. Save this file as app/main.py
# 3. Save the other files below in their respective locations.
# 4. Install dependencies: pip install -r requirements.txt
# 5. Run the server from the root directory `file-server-api/`:
#    uvicorn app.main:app --reload

