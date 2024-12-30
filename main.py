from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import auth, habits, analytics

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Frontend URL
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