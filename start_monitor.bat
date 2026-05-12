@echo off
echo 🚀 PHASMA AI 24/7 TRADING MONITOR
echo =================================
echo.
echo Starting continuous monitoring for trading opportunities...
echo.

python "%~dp0scripts\monitoring\monitor.py" %1

echo.
echo ✅ Monitoring session complete
pause
