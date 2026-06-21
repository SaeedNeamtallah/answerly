@echo off
REM RAGMind start script with Next.js frontend launcher
setlocal
chcp 65001 >nul

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "ROOT=%%~fI"
pushd "%ROOT%"

set "NEXT_FRONTEND_DIR=%ROOT%\frontend-next"
set "NEXT_FRONTEND_PORT=3001"
set "NEXT_FRONTEND_URL=http://localhost:%NEXT_FRONTEND_PORT%/login"
set "NEXT_WINDOW_TITLE=RAGMind Next Frontend"
set "LOGS_DIR=%ROOT%\uploads\logs"
set "RUN_LOG=%LOGS_DIR%\newstart.log"
set "NEXT_LOG=%LOGS_DIR%\frontend_next.log"
set "NEXT_CMD="
set "PNPM_CMD="
set "NPM_CMD="

if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"
>> "%RUN_LOG%" echo.
>> "%RUN_LOG%" echo ========================================
>> "%RUN_LOG%" echo [NEWSTART] %date% %time%
>> "%RUN_LOG%" echo ========================================

call :log "========================================"
call :log "   RAGMind - Start + Next Frontend"
call :log "========================================"
call :log "."

if not exist "%NEXT_FRONTEND_DIR%\package.json" (
    call :log "[ERROR] frontend-next workspace was not found at:"
    call :log "        %NEXT_FRONTEND_DIR%"
    goto :fail
)

where node.exe >nul 2>&1
if errorlevel 1 (
    call :log "[ERROR] Node.js is not available in PATH."
    call :log "[HINT] Install Node.js 20+ and open a new terminal before running newstart.bat."
    goto :fail
)

for /f "delims=" %%V in ('node --version 2^>nul') do call :log "[INFO] Detected Node.js %%V"

call :resolve_package_manager
if not defined NEXT_CMD (
    call :log "[ERROR] Neither pnpm nor npm is available in PATH."
    goto :fail
)

call :log "[INFO] Starting backend stack via scripts\dev\start.bat"
set "SKIP_SCRIPT_PAUSE=1"
call "%ROOT%\scripts\dev\start.bat" %*
if errorlevel 1 (
    call :log "[ERROR] Base stack startup failed."
    goto :fail
)

netstat -ano | findstr /R /C:":%NEXT_FRONTEND_PORT% .*LISTENING" >nul 2>&1
if errorlevel 1 (
    >> "%NEXT_LOG%" echo.
    >> "%NEXT_LOG%" echo ========================================
    >> "%NEXT_LOG%" echo [NEXT FRONTEND LOG SESSION] %date% %time%
    >> "%NEXT_LOG%" echo ========================================
    call :log "[INFO] Starting Next.js frontend on %NEXT_FRONTEND_URL%"
    call :log "[INFO] Next frontend logs: %NEXT_LOG%"
    start "%NEXT_WINDOW_TITLE%" /min cmd /d /c "cd /d "%NEXT_FRONTEND_DIR%" && %NEXT_CMD% 1>> "%NEXT_LOG%" 2>&1"
) else (
    call :log "[INFO] Next.js frontend already listening on port %NEXT_FRONTEND_PORT%"
)

call :log "[INFO] Waiting for Next.js frontend readiness..."
for /l %%A in (1,1,90) do (
    curl.exe -fsS "%NEXT_FRONTEND_URL%" >nul 2>&1
    if not errorlevel 1 goto :frontend_ready
    timeout /t 1 /nobreak <nul >nul 2>&1 || ping 127.0.0.1 -n 2 >nul 2>&1
)

call :log "[ERROR] Next.js frontend did not become reachable in time."
goto :fail

:frontend_ready
call :log "[STATUS] Next frontend ready"
call :log "[INFO] Opening %NEXT_FRONTEND_URL%"
start "" "%NEXT_FRONTEND_URL%" >nul 2>&1

call :log "."
call :log "========================================"
call :log "[✓] RAGMind backend + Next frontend are running"
call :log "========================================"
call :log "."
call :log "Backend + legacy frontend: scripts\dev\start.bat"
call :log "Next frontend:            %NEXT_FRONTEND_URL%"
call :log "Logs:                     %RUN_LOG%"
call :log "Next log:                 %NEXT_LOG%"
call :log "."
goto :done

:resolve_package_manager
for /f "delims=" %%P in ('where pnpm.cmd 2^>nul') do (
    set "PNPM_CMD=%%P"
    goto :pnpm_found
)
goto :check_npm

:pnpm_found
if defined PNPM_CMD (
    set "NEXT_CMD="%PNPM_CMD%" dev"
    goto :eof
)

:check_npm
for /f "delims=" %%N in ('where npm.cmd 2^>nul') do (
    set "NPM_CMD=%%N"
    goto :npm_found
)
goto :eof

:npm_found
if defined NPM_CMD (
    set "NEXT_CMD="%NPM_CMD%" run dev"
    goto :eof
)
goto :eof

:fail
if not defined SKIP_SCRIPT_PAUSE pause
popd
endlocal
exit /b 1

:done
if not defined SKIP_SCRIPT_PAUSE pause
popd
endlocal
exit /b 0

:log
echo %~1
>> "%RUN_LOG%" echo %~1
goto :eof
