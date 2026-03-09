@echo off
echo ===================================================
echo       Building The Great Silence Game
echo ===================================================
echo.
echo Cleaning previous builds...
rmdir /s /q dist build

echo.
echo Running PyInstaller...
python -m PyInstaller TheGreatSilence.spec --clean --noconfirm

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Build failed! Please check the output above.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo ===================================================
echo [SUCCESS] Build complete!
echo Executable location: dist\TheGreatSilence\TheGreatSilence.exe
echo ===================================================
echo.
pause