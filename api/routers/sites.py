from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from api.database import get_db
from api.models.site import Site
from api.models.user import User, UserRole
from api.schemas.site import SiteCreate, SiteUpdate, SiteResponse
from api.dependencies import get_current_user, require_roles

router = APIRouter()

@router.post("/sites", response_model=SiteResponse)
async def create_site(site_data: SiteCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_roles("ADMIN"))):
    new_site = Site(**site_data.dict())
    db.add(new_site)
    await db.commit()
    await db.refresh(new_site)
    return new_site

@router.get("/sites")
async def list_sites(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Site))
    sites = result.scalars().all()
    return [{"site_id": s.site_id, "site_name": s.site_name, "site_type": s.site_type.value, "address": s.address} for s in sites]

@router.get("/sites/{site_id}", response_model=SiteResponse)
async def get_site(site_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    result = await db.execute(select(Site).where(Site.site_id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return site

@router.put("/sites/{site_id}", response_model=SiteResponse)
async def update_site(site_id: int, site_data: SiteUpdate, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_roles("ADMIN"))):
    result = await db.execute(select(Site).where(Site.site_id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    for key, value in site_data.dict(exclude_unset=True).items():
        setattr(site, key, value)
    await db.commit()
    await db.refresh(site)
    return site

@router.delete("/sites/{site_id}")
async def delete_site(site_id: int, db: AsyncSession = Depends(get_db), current_user: User = Depends(require_roles("ADMIN"))):
    result = await db.execute(select(Site).where(Site.site_id == site_id))
    site = result.scalar_one_or_none()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    await db.delete(site)
    await db.commit()
    return {"message": "Site deleted"}

@router.get("/roles")
async def list_roles(current_user: User = Depends(get_current_user)):
    return [{"value": r.value, "label": r.value} for r in UserRole]
