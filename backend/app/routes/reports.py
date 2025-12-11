import json
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import Optional

from app.database import get_db
from app.models.user import User
from app.models.report import Report, ReportStatus
from app.services.utils import save_upload_file, extract_exif_location
from app.services.ai_service import analyze_report_text

router = APIRouter()

@router.post("/reports/", status_code=202)
async def submit_report(
    background_tasks: BackgroundTasks,
    telegram_id: str = Form(...),
    phone_number: str = Form(...),
    description: str = Form(...),
    address: Optional[str] = Form(None),
    latitude: Optional[float] = Form(None),
    longitude: Optional[float] = Form(None),
    image: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Ingestion endpoint for Telegram bot microservice.
    Receives report data, saves image, and triggers background processing.
    """
    
    result = await db.execute(select(User).where(User.telegram_id == int(telegram_id)))
    user = result.scalars().first()
    
    if not user:
        user = User(telegram_id=int(telegram_id), phone_number=phone_number)
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    web_image_path, abs_image_path = save_upload_file(image)
    
    lat = latitude
    lon = longitude

    # If lat/lon not provided in form, try to extract from EXIF
    if lat is None or lon is None:
        print(f"DEBUG: Lat/Lon not explicitly provided. Attempting EXIF extraction for {abs_image_path}")
            
    if lat is None or lon is None:
        exif_lat, exif_lon = extract_exif_location(abs_image_path)
        if lat is None: lat = exif_lat
        if lon is None: lon = exif_lon

    new_report = Report(
        user_id=user.id,
        image_url=web_image_path,
        original_description=description,
        address=address,
        latitude=lat,
        longitude=lon,
        status=ReportStatus.RECEIVED
    )
    db.add(new_report)
    await db.commit()
    await db.refresh(new_report)
    
    background_tasks.add_task(process_report_ai, new_report.id, description)
    
    return {"report_id": new_report.id, "status": "processing"}

async def process_report_ai(report_id: int, description: str):
    """
    Background task to run AI analysis and update the report.
    """
    print(f"[{report_id}] Starting background AI processing...")
    from app.database import SessionLocal
    async with SessionLocal() as db:
        try:
            print(f"[{report_id}] Sending text to Gemini...")
            ai_result = await analyze_report_text(description)
            print(f"[{report_id}] Gemini Result: {ai_result}")
            
            result = await db.execute(select(Report).where(Report.id == report_id))
            report = result.scalars().first()
            
            if report:
                report.title = ai_result.get("title")
                report.generated_description = ai_result.get("description")
                report.category = ai_result.get("category")
                report.priority = ai_result.get("priority")
                
                await db.commit()
                print(f"[{report_id}] Report updated successfully.")
            else:
                print(f"[{report_id}] Report not found in DB!")
        except Exception as e:
            print(f"[{report_id}] Error processing report: {e}")
            import traceback
            traceback.print_exc()
