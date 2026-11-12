@echo off
cd /d "%~dp0"
py -m pip install -r requirements-web.txt
if errorlevel 1 pause & exit /b 1
py -m uvicorn web_api:app --host 127.0.0.1 --port 8000
pause
