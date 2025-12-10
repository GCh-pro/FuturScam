@echo off
REM FuturScam ETL - Continuous Runner (Batch)
REM Execute ETL in continuous loop mode

setlocal enabledelayedexpansion

set INTERVAL_MINUTES=60
if not "%1"=="" set INTERVAL_MINUTES=%1

echo ================================================================================
echo FuturScam ETL - Continuous Mode
echo Interval: Every %INTERVAL_MINUTES% minutes
echo Press Ctrl+C to stop
echo ================================================================================
echo.

set RUN_COUNT=0

:LOOP
set /a RUN_COUNT+=1

echo.
echo ================================================================================
echo [RUN #%RUN_COUNT%] Starting ETL execution at %DATE% %TIME%
echo ================================================================================
echo.

cd /d "%~dp0"
python src\main.py

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ================================================================================
    echo [RUN #%RUN_COUNT%] ETL completed successfully
    echo ================================================================================
) else (
    echo.
    echo ================================================================================
    echo [RUN #%RUN_COUNT%] ETL failed with error code %ERRORLEVEL%
    echo ================================================================================
)

echo.
echo [SCHEDULER] Waiting %INTERVAL_MINUTES% minutes before next run...
timeout /t %INTERVAL_MINUTES%00 /nobreak

goto LOOP
