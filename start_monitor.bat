@echo off
echo PHASMA AI 24/7 TRADING MONITOR
echo =================================
echo.
echo Starting continuous monitoring (same as: python main.py --interval N)
echo Auto-restart on fatal crash is enabled. Press Ctrl+C to stop.
echo.

if "%~1"=="" (
  python "%~dp0main.py" --interval 5
) else (
  python "%~dp0main.py" --interval %1
)

echo.
echo Monitoring session complete
pause
