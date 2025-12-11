from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List, Optional

from app.database import get_db
from app.models.report import Report, ReportStatus

router = APIRouter()

@router.get("/admin/reports")
async def get_admin_reports(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all reports with optional filtering.
    """
    query = select(Report)
    
    if status:
        query = query.where(Report.status == status)
    if priority:
        query = query.where(Report.priority == priority)
    if category:
        query = query.where(Report.category == category)
        
    query = query.offset(skip).limit(limit).order_by(Report.created_at.desc())
    
    result = await db.execute(query)
    reports = result.scalars().all()
    return reports

@router.get("/admin/reports/{report_id}")
async def get_report_detail(report_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalars().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report

@router.patch("/admin/reports/{report_id}")
async def update_report_status(report_id: int, status: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Report).where(Report.id == report_id))
    report = result.scalars().first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    if status not in ReportStatus.__members__.values():
        raise HTTPException(status_code=400, detail="Invalid status")
        
    report.status = status
    await db.commit()
    await db.refresh(report)
    return report
