@echo off
REM SMPF Fly.io Deploy Helper for Windows
REM Run this after installing Fly CLI

echo ========================================
echo SMPF Backend Deploy to Fly.io
echo ========================================
echo.

set SMFP_DIR=C:\Users\RudiOosthuizen\smpf

cd /d %SMFP_DIR%

echo [1/6] Checking Fly CLI...
fly version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Fly CLI not found. Install from https://fly.io/install
    exit /b 1
)

echo [2/6] Logging into Fly.io...
fly auth login

echo [3/6] Creating app (if not exists)...
fly apps list | findstr smpf-backend >nul 2>&1
if errorlevel 1 (
    fly apps create smpf-backend
)

echo [4/6] Creating persistent volume for data...
fly volumes list --app smpf-backend | findstr smpf_data >nul 2>&1
if errorlevel 1 (
    fly volumes create smpf_data --size 1 --app smpf-backend --region jnb
)

echo [5/6] Setting secrets...
echo Add your secrets now. Press any key when ready...
pause >nul

echo [6/6] Deploying...
fly deploy

echo.
echo ========================================
echo Done! Your backend is live at:
echo https://smpf-backend.fly.dev
echo ========================================
pause
