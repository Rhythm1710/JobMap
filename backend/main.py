# Import Dependencies
from fastapi import FastAPI
from database import engine, Base

from routes.user_routes import user_router
from routes.job_routes import job_router
from routes.auth_routes import auth_router
from routes.admin_routes import admin_router

# Backend Application Initilization
app = FastAPI(title="JobMap Backend")

# Connection with the database
Base.metadata.create_all(bind=engine)

# Root Endpoint
@app.get("/")
def server_started():
    return {"message": "Server started successfully"}

# Include the routes
app.include_router(user_router)
app.include_router(job_router)
app.include_router(auth_router)
app.include_router(admin_router)
