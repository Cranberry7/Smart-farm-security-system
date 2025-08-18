from fastapi import FastAPI
from app.routes import auth, sensor, user_routes, security, devices  # Import routes
from app.database import engine
from app import models  # Ensure models are imported
from fastapi.middleware.cors import CORSMiddleware
from app.security_middleware import SecurityMiddleware

# Ensure tables are created in the database
models.Base.metadata.create_all(bind=engine)

# Initialize FastAPI app
app = FastAPI()

# Include route modules
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(sensor.router, prefix="/sensor", tags=["Sensor data"])
app.include_router(user_routes.router, prefix="/users", tags=["Users"])
app.include_router(security.router, prefix="/security", tags=["Security Monitoring"])
app.include_router(devices.router, prefix="/devices", tags=["Device Management"])

@app.get("/")
def root():
    return {"message": "Smart Farm Backend is running!"}

# Add security middleware (IDS/IPS)
app.add_middleware(SecurityMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Run the server (Use `uvicorn app.main:app --reload` instead)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
