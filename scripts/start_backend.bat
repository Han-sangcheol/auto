@echo off
echo Starting CleonAI Backend API Server...
echo.

cd backend
call venv\Scripts\activate
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause

