@echo off
cd C:\Task\asset-management
call venv\Scripts\activate
docker-compose up -d postgres
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000