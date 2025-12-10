# FuturScam ETL - Continuous Runner
# Execute ETL in continuous loop mode

param(
    [int]$IntervalMinutes = 60,  # Default: run every hour
    [switch]$Help
)

if ($Help) {
    Write-Host @"
FuturScam ETL Continuous Runner

Usage: .\run_etl_continuous.ps1 [-IntervalMinutes <minutes>] [-Help]

Parameters:
  -IntervalMinutes   Interval between runs in minutes (default: 60)
  -Help             Show this help message

Examples:
  .\run_etl_continuous.ps1                    # Run every hour
  .\run_etl_continuous.ps1 -IntervalMinutes 30  # Run every 30 minutes
  .\run_etl_continuous.ps1 -IntervalMinutes 5   # Run every 5 minutes

Press Ctrl+C to stop the continuous execution.
"@
    exit 0
}

$ErrorActionPreference = "Continue"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host "FuturScam ETL - Continuous Mode" -ForegroundColor Cyan
Write-Host "Interval: Every $IntervalMinutes minutes" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop" -ForegroundColor Cyan
Write-Host "================================================================================" -ForegroundColor Cyan
Write-Host ""

$runCount = 0

while ($true) {
    $runCount++
    $startTime = Get-Date
    
    Write-Host ""
    Write-Host "================================================================================" -ForegroundColor Yellow
    Write-Host "[RUN #$runCount] Starting ETL execution at $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Yellow
    Write-Host "================================================================================" -ForegroundColor Yellow
    Write-Host ""
    
    try {
        # Execute ETL
        python src\main.py
        
        $endTime = Get-Date
        $duration = ($endTime - $startTime).TotalSeconds
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-Host "================================================================================" -ForegroundColor Green
            Write-Host "[RUN #$runCount] ETL completed successfully in $([math]::Round($duration, 2)) seconds" -ForegroundColor Green
            Write-Host "================================================================================" -ForegroundColor Green
        } else {
            Write-Host ""
            Write-Host "================================================================================" -ForegroundColor Red
            Write-Host "[RUN #$runCount] ETL failed with error code $LASTEXITCODE after $([math]::Round($duration, 2)) seconds" -ForegroundColor Red
            Write-Host "================================================================================" -ForegroundColor Red
        }
        
    } catch {
        Write-Host ""
        Write-Host "================================================================================" -ForegroundColor Red
        Write-Host "[RUN #$runCount] ETL failed with exception: $_" -ForegroundColor Red
        Write-Host "================================================================================" -ForegroundColor Red
    }
    
    # Calculate next run time
    $nextRun = (Get-Date).AddMinutes($IntervalMinutes)
    $waitSeconds = $IntervalMinutes * 60
    
    Write-Host ""
    Write-Host "[SCHEDULER] Next run scheduled at $(Get-Date $nextRun -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
    Write-Host "[SCHEDULER] Waiting $IntervalMinutes minutes..." -ForegroundColor Cyan
    
    # Wait with countdown
    for ($i = $waitSeconds; $i -gt 0; $i--) {
        $minutesLeft = [math]::Floor($i / 60)
        $secondsLeft = $i % 60
        Write-Progress -Activity "Waiting for next run" -Status "Time remaining: $minutesLeft min $secondsLeft sec" -PercentComplete ((($waitSeconds - $i) / $waitSeconds) * 100)
        Start-Sleep -Seconds 1
    }
    
    Write-Progress -Activity "Waiting for next run" -Completed
}
