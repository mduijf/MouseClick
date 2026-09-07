@echo off
setlocal
cd /d "%~dp0"

echo === MouseClick build ===
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo FOUT: Python niet gevonden. Installeer Python 3.10+ van python.org
    pause
    exit /b 1
)

echo Installeren PyInstaller...
python -m pip install --upgrade pip pyinstaller -q

echo Bouwen MouseClick.exe...
python -m PyInstaller MouseClick.spec --noconfirm --clean

if exist "dist\MouseClick.exe" (
    echo.
    echo Klaar: dist\MouseClick.exe
    copy /Y clicks.json dist\clicks.json >nul 2>&1
    echo Voorbeeldconfig gekopieerd naar dist\clicks.json
) else (
    echo.
    echo FOUT: Build mislukt.
)

echo.
pause
