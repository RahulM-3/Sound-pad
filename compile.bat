@echo off
echo ==============================================
echo       SOUNDPAD COMPILE SCRIPT
echo ==============================================
echo.
echo Installing PyInstaller inside virtual environment if needed...
pip install pyinstaller

echo.
echo Starting the python icon generator and PyInstaller build...
python build.py

echo.
echo ==============================================
echo Process Complete. Look inside the 'dist' folder.
echo ==============================================
pause
