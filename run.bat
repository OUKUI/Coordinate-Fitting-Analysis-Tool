@echo off
cd /d "%~dp0"

"C:\Users\kui_o\AppData\Local\hermes\hermes-agent\venv\Scripts\pythonw.exe" "%~dp0main.py" 2>"%~dp0error.log"

if %errorlevel% neq 0 (
    start notepad "%~dp0error.log"
)
