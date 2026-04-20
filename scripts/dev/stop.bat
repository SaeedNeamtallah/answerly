@echo off
REM RAGMind Unified Stop Script
setlocal
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "ROOT=%%~fI"
pushd "%ROOT%"
set "LOGS_DIR=%ROOT%\uploads\logs"
set "RUN_LOG=%LOGS_DIR%\stop.log"
set "STACK_STATE_LOG=%LOGS_DIR%\docker_ps.log"

if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"
>> "%RUN_LOG%" echo.
>> "%RUN_LOG%" echo ========================================
>> "%RUN_LOG%" echo [STOP] %date% %time%
>> "%RUN_LOG%" echo ========================================

call :log "========================================"
call :log "   RAGMind - Stop"
call :log "========================================"
call :log "."

call :log "[INFO] Closing frontend window if it is running..."
taskkill /FI "WINDOWTITLE eq RAGMind Frontend" /T /F >nul 2>&1
call :log "[INFO] Closing Docker log streamer if it is running..."
taskkill /FI "WINDOWTITLE eq RAGMind Docker Logs" /T /F >nul 2>&1

set "DOCKER_INFO_TMP=%TEMP%\ragmind_docker_info_%RANDOM%.log"
docker info > "%DOCKER_INFO_TMP%" 2>&1
if errorlevel 1 (
    call :log "[WARNING] Docker Desktop is not running or not ready."
    call :docker_info_hint "%DOCKER_INFO_TMP%"
    del "%DOCKER_INFO_TMP%" >nul 2>&1
    call :log "[INFO] Frontend and log windows were closed."
    call :log "[INFO] Start Docker Desktop if you need to manage running containers."
    goto :done
)
del "%DOCKER_INFO_TMP%" >nul 2>&1

>> "%STACK_STATE_LOG%" echo.
>> "%STACK_STATE_LOG%" echo ========================================
>> "%STACK_STATE_LOG%" echo [STACK STATUS BEFORE STOP] %date% %time%
>> "%STACK_STATE_LOG%" echo ========================================
>> "%STACK_STATE_LOG%" echo [COMMAND] docker compose -f docker/docker-compose.yml ps
docker compose -f docker/docker-compose.yml ps >> "%STACK_STATE_LOG%" 2>&1

call :log "[INFO] Stopping Docker services..."
>> "%RUN_LOG%" echo [COMMAND] docker compose -f docker/docker-compose.yml down
docker compose -f docker/docker-compose.yml down >> "%RUN_LOG%" 2>&1
if errorlevel 1 (
    call :log "[ERROR] Failed to stop the Docker stack."
    goto :fail
)

>> "%STACK_STATE_LOG%" echo [COMMAND] docker compose -f docker/docker-compose.yml ps -a
docker compose -f docker/docker-compose.yml ps -a >> "%STACK_STATE_LOG%" 2>&1

call :log "."
call :log "========================================"
call :log "[✓] RAGMind is stopped"
call :log "========================================"
call :log "."
call :log "Stop log:  %RUN_LOG%"
call :log "Stack PS:  %STACK_STATE_LOG%"
call :log "Data is preserved in Docker volumes."
call :log "To also remove volumes:"
call :log "  docker compose -f docker/docker-compose.yml down -v"
call :log "."
goto :done

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

:docker_info_hint
set "DOCKER_INFO_FILE=%~1"
if not exist "%DOCKER_INFO_FILE%" goto :eof
findstr /I /C:"Wsl/Service/CreateInstance/E_FAIL" /C:"WSL integration" /C:"The distribution failed to start" "%DOCKER_INFO_FILE%" >nul 2>&1
if not errorlevel 1 (
    call :log "[HINT] Detected a Docker Desktop WSL integration failure."
    call :log "[HINT] Run: wsl --shutdown"
    call :log "[HINT] Then run: wsl --update"
    call :log "[HINT] Restart Docker Desktop. If needed, toggle Ubuntu integration in Docker Desktop settings."
)
goto :eof

:log
echo %~1
>> "%RUN_LOG%" echo %~1
goto :eof
