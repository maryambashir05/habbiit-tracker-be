from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, habits, analytics
import os
from typing import List

app = FastAPI()

def get_allowed_origins() -> List[str]:
    origins_str = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173")
    return [origin.strip() for origin in origins_str.split(",")]

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(habits.router)
app.include_router(analytics.router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"} 