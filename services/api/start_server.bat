@echo off
cd /d "C:\Users\thepr\Downloads\Luthiers ToolBox\services\api"
call .venv\Scripts\activate.bat
python -m uvicorn app.main:app --port 8000 --reload
pause
