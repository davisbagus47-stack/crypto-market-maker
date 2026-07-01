@echo off
setlocal
cd /d "%~dp0backend"

if not exist ".venv\Scripts\python.exe" (
  where python >nul 2>nul
  if %errorlevel%==0 (
    set BOOTSTRAP_PYTHON=python
  ) else (
    set BOOTSTRAP_PYTHON=py
  )
  %BOOTSTRAP_PYTHON% -m venv .venv
)

set PYTHON=.venv\Scripts\python.exe
%PYTHON% -m pip install -r requirements.txt
%PYTHON% -m uvicorn main:app --reload --host 127.0.0.1 --port 8000
