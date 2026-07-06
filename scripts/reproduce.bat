@echo off
REM One-command reproduction script for Agile-SOFL error prevention experiments
cd /d %~dp0..

echo [1/5] Installing Python dependencies...
pip install -e . -q

echo [2/5] Building Agile-SOFL parser...
cd vendor\agile-sofl-toolchain
call npm install
call npm run build:parser
cd ..\..

echo [3/5] Building benchmark...
python scripts\build_benchmark.py

echo [4/5] Running experiments...
python experiments\run_all.py --repeats 2

echo [5/5] Analyzing results...
for /f "delims=" %%i in ('dir /b /od artifacts\run_* ^| findstr /r "run_"') do set LATEST=%%i
python experiments\analyze.py artifacts\%LATEST%

echo Done. See artifacts\%LATEST%\analysis\
