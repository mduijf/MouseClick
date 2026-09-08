@echo off
setlocal
cd /d "%~dp0"

echo === Yellowspot MouseClick build ===
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo FOUT: Python niet gevonden. Installeer Python 3.10+ van python.org
    pause
    exit /b 1
)

for /f "delims=" %%v in ('python -c "from version import version_label; print(version_label())"') do set VERSION=%%v
echo Versie: %VERSION%
echo.

echo Installeren dependencies...
python -m pip install --upgrade pip pyinstaller pystray Pillow -q

echo Bouwen YellowspotMouseClick-%VERSION%.exe...
python -m PyInstaller MouseClick.spec --noconfirm --clean
python write_dist_version.py
copy /Y clicks.json dist\clicks.json >nul 2>&1

for %%f in (dist\YellowspotMouseClick-v*.exe) do (
    echo.
    echo Klaar: %%f
    echo Versie: dist\version.txt
    goto :done
)

echo.
echo FOUT: Build mislukt.

:done
echo.
pause
