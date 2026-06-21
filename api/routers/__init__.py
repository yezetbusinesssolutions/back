from fastapi import APIRouter
from . import health, auth, assembly, sales, audit, users, sites

router = APIRouter()

router.include_router(health.router, prefix="/health", tags=["health"])
router.include_router(auth.router, prefix="/auth", tags=["auth"])
router.include_router(users.router, prefix="/users", tags=["users"])
router.include_router(sites.router, prefix="/sites", tags=["sites"])
router.include_router(assembly.router, prefix="/assembly", tags=["assembly"])
router.include_router(sales.router, prefix="/sales", tags=["sales"])
router.include_router(audit.router, prefix="/audit", tags=["audit"])
