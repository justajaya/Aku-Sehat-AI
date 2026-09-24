@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (py -3.12 -m venv .venv || goto :error)
.venv\Scripts\python.exe -m pip install -r requirements.txt || goto :error
.venv\Scripts\python.exe -m streamlit run app.py
pause
exit /b 0
:error
echo Gagal. Pastikan Python 3.12 terpasang.
pause
