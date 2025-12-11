from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from app.database import get_db
from app.models.report import Report, ReportStatus

router = APIRouter()

@router.get("/public/reports")
async def get_public_reports(
    db: AsyncSession = Depends(get_db)
):
    """
    Get public facing reports. Sanitize sensitive data.
    """
    query = select(Report).order_by(Report.created_at.desc())
    result = await db.execute(query)
    reports = result.scalars().all()
    
    public_reports = []
    for r in reports:
        public_reports.append({
            "id": r.id,
            "title": r.title,
            "category": r.category,
            "status": r.status,
            "latitude": r.latitude,
            "longitude": r.longitude,
            "image_url": r.image_url,
            "created_at": r.created_at,
            "address": r.address
        })
        
    return public_reports
