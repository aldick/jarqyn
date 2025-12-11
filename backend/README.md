# Pavlodar Problem Reporting System (Backend)

Backend service for processing city problem reports via Telegram and providing data to Admin Dashboard and Public Map.

## Technology
- **Framework**: FastAPI
- **DB**: SQLite (Prototype) / PostgreSQL (Production) via SQLAlchemy Async
- **AI**: Google Gemini (Text Analysis)

## Features
- **Ingestion**: Accepts reports from Telegram Bot microservice.
- **Geolocation**: Extracts from Request or Image EXIF.
- **AI Analysis**: Categorizes and prioritizes reports based on user description (in Russian).
- **Admin API**: Manage report status.
- **Public API**: Transparency feed.

## Quick Start
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```
