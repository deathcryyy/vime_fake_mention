@echo off
title VimeMention - Sborka EXE

echo.
echo  ================================
echo    VimeMention - Sborka EXE
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

echo  [1/3] Ustanovka zavisimostej...
pip install requests beautifulsoup4 pyinstaller --quiet --disable-pip-version-check
if %errorlevel% neq 0 (
    echo  OSHIBKA: Ne udalos ustanovit zavisimosti.
    pause
    exit /b 1
)

echo  [2/3] Sborka EXE...
pyinstaller --onefile --windowed --name "VimeMention" --distpath dist --workpath build_tmp --specpath build_tmp src\gui.py
if %errorlevel% neq 0 (
    echo  OSHIBKA: Sborka ne udalas.
    pause
    exit /b 1
)

if exist build_tmp rmdir /s /q build_tmp

echo.
echo  [3/3] Gotovo!
echo.
echo  EXE fajl: dist\VimeMention.exe
echo.
pause
