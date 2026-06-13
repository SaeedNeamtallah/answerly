@echo off
echo [INFO] newstart.bat has been deprecated. start.bat now launches the Next.js frontend directly!
echo [INFO] Redirecting to scripts\dev\start.bat...
call "%~dp0start.bat" %*
