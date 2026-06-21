import sys
import os
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, "/")

from fastapi import FastAPI
from api.middleware.cors import setup_cors
from api.routers import health, auth, assembly, sales, audit, users, sites

app = FastAPI(title="Motor Assembly & Sales System", version="1.0.0")

setup_cors(app)

# Serve uploaded files
uploads_path = "/app/uploads"
if os.path.exists(uploads_path):
    app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")

app.include_router(health.router, prefix="/api/v1/health", tags=["health"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1", tags=["users"])
app.include_router(sites.router, prefix="/api/v1", tags=["sites"])
app.include_router(assembly.router, prefix="/api/v1/assembly", tags=["assembly"])
app.include_router(sales.router, prefix="/api/v1/sales", tags=["sales"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["audit"])