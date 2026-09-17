from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.router import router as api_router
from app.models import database, schema

# Create DB tables
schema.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="NavCare API", description="Backend for Hospital Wayfinding Platform", version="1.0.0")

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Update this in production to match frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")

@app.get("/")
def read_root():
    return {"message": "Welcome to NavCare API"}

@app.get("/api/health")
def health_check():
    return {"status": "ok"}
