@echo off
echo ================================================
echo   Vibe Expenses — Build standalone .exe
echo ================================================
echo.

echo [1/2] Installing PyInstaller...
pip install pyinstaller --quiet
if errorlevel 1 (
    echo ERROR: pip install failed. Make sure Python is on your PATH.
    pause & exit /b 1
)

echo [2/2] Building VibeExpenses.exe...
python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name "VibeExpenses" ^
    --collect-all matplotlib ^
    --collect-all PyQt6 ^
    --clean ^
    main.py

if errorlevel 1 (
    echo.
    echo ERROR: Build failed. See output above.
    pause & exit /b 1
)

echo.
echo ================================================
echo   SUCCESS!  dist\VibeExpenses.exe is ready.
echo.
echo   Copy VibeExpenses.exe to any folder you like.
echo   Your expenses.db will be created / used in
echo   the same folder as the .exe — data is safe.
echo ================================================
pause
