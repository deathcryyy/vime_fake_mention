@echo off
title VimeMention

echo.
echo  ================================
echo         VimeMention
echo  ================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  OSHIBKA: Python ne najden!
    echo  Skachaj Python s https://python.org
    echo  Pri ustanovke postavj galochku "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo  [1/2] Ustanovka zavisimostej...
pip install requests beautifulsoup4 --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo  OSHIBKA: Ne udalos ustanovit zavisimosti.
    pause
    exit /b 1
)

echo  [2/2] Zapusk VimeMention...
echo.
python src\gui.py

if %errorlevel% neq 0 (
    echo.
    echo  Programma zavershilas s oshibkoj.
    pause
)
