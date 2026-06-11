@echo off
REM RAGMind Unified Start Script
setlocal
chcp 65001 >nul
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "ROOT=%%~fI"
pushd "%ROOT%"

set "FRONTEND_PORT=8080"
set "BACKEND_HEALTH_URL=http://127.0.0.1:8000/health/full"
set "FRONTEND_URL=http://localhost:%FRONTEND_PORT%/login.html?api=http://localhost:8000"
set "FRONTEND_WINDOW_TITLE=RAGMind Frontend"
set "STACK_LOG_WINDOW_TITLE=RAGMind Docker Logs"
set "FRONTEND_PYTHON="
set "BACKEND_HEALTH_TIMEOUT_SECONDS=15"
set "FRONTEND_READY_TIMEOUT_SECONDS=30"
set "LOGS_DIR=%ROOT%\uploads\logs"
set "RUN_LOG=%LOGS_DIR%\start.log"
set "STACK_LOG=%LOGS_DIR%\docker_stack.log"
set "FRONTEND_LOG=%LOGS_DIR%\frontend.log"
set "STACK_STATE_LOG=%LOGS_DIR%\docker_ps.log"
set "COMPOSE_UP_ARGS=up -d"
set "COMPOSE_PROFILE_ARGS="
set "START_MODE=normal"
if not defined FRONTEND_MODE set "FRONTEND_MODE=local"
if /I "%FRONTEND_MODE%"=="docker" (
    set "COMPOSE_PROFILE_ARGS=--profile docker-frontend"
    set "FRONTEND_URL=http://localhost/login.html?api=http://localhost:8000"
) else if /I not "%FRONTEND_MODE%"=="local" (
    echo [ERROR] FRONTEND_MODE must be local or docker.
    popd
    endlocal
    exit /b 1
)

if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"
>> "%RUN_LOG%" echo.
>> "%RUN_LOG%" echo ========================================
>> "%RUN_LOG%" echo [START] %date% %time%
>> "%RUN_LOG%" echo ========================================

call :log "========================================"
call :log "   RAGMind - Start"
call :log "========================================"
call :log "."

if /I "%~1"=="--build" (
    set "COMPOSE_UP_ARGS=up -d --build"
    set "START_MODE=build"
) else if not "%~1"=="" (
    call :log "[ERROR] Unsupported argument: %~1"
    call :log "Usage:"
    call :log "  scripts\dev\start.bat"
    call :log "  scripts\dev\start.bat --build"
    goto :fail
)

docker --version >nul 2>&1
if errorlevel 1 (
    call :log "[ERROR] Docker is not installed or not available in PATH."
    call :log "Install Docker Desktop, then run scripts\dev\setup.bat if needed."
    goto :fail
)

set "DOCKER_INFO_TMP=%TEMP%\ragmind_docker_info_%RANDOM%.log"
docker info > "%DOCKER_INFO_TMP%" 2>&1
if errorlevel 1 (
    call :log "[ERROR] Docker Desktop is not running or not ready."
    call :docker_info_hint "%DOCKER_INFO_TMP%"
    del "%DOCKER_INFO_TMP%" >nul 2>&1
    goto :fail
)
del "%DOCKER_INFO_TMP%" >nul 2>&1

if exist "%ROOT%\venv\Scripts\python.exe" (
    set "FRONTEND_PYTHON=%ROOT%\venv\Scripts\python.exe"
) else (
    python --version >nul 2>&1
    if errorlevel 1 (
        call :log "[ERROR] Python was not found."
        call :log "Run scripts\dev\setup.bat first."
        goto :fail
    )
    set "FRONTEND_PYTHON=python"
)

if /I "%START_MODE%"=="build" (
    call :log "[INFO] Building and starting Docker services..."
) else (
    call :log "[INFO] Starting Docker services without rebuild..."
    call :log "[INFO] Use scripts\dev\start.bat --build only when image inputs changed."
)
>> "%RUN_LOG%" echo [COMMAND] docker compose -f docker/docker-compose.yml %COMPOSE_PROFILE_ARGS% %COMPOSE_UP_ARGS%
docker compose -f docker/docker-compose.yml %COMPOSE_PROFILE_ARGS% %COMPOSE_UP_ARGS% >> "%RUN_LOG%" 2>&1
if errorlevel 1 (
    call :log "[ERROR] Failed to start the Docker stack."
    call :log "Inspect logs in %RUN_LOG% or run: docker compose -f docker/docker-compose.yml logs --tail=200"
    goto :fail
)
call :log "[STATUS] Stack up"

call :log "[INFO] Waiting for full backend readiness check..."
for /l %%A in (1,1,180) do (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $response = Invoke-RestMethod -Uri '%BACKEND_HEALTH_URL%' -TimeoutSec %BACKEND_HEALTH_TIMEOUT_SECONDS%; if ($response.status -eq 'healthy') { exit 0 } } catch { }; exit 1" >nul 2>&1
    if not errorlevel 1 goto :backend_ready
    timeout /t 1 /nobreak >nul
)
call :log "[WARNING] Host health probe failed. Trying backend health from inside container..."
docker exec ragmind-backend python -c "import json,sys,urllib.request; data=json.load(urllib.request.urlopen('http://127.0.0.1:8000/health/full', timeout=8)); sys.exit(0 if data.get('status')=='healthy' else 1)" >nul 2>&1
if not errorlevel 1 (
    call :log "[WARNING] Backend is healthy inside container, but host access to %BACKEND_HEALTH_URL% failed."
    call :log "[WARNING] Continuing startup. Check local networking/proxy rules if host API access remains unavailable."
    goto :backend_ready
)
call :log "[ERROR] Backend did not reach full healthy state in time."
>> "%RUN_LOG%" echo [COMMAND] docker compose -f docker/docker-compose.yml logs --tail=200 --no-color
docker compose -f docker/docker-compose.yml logs --tail=200 --no-color >> "%RUN_LOG%" 2>&1
call :log "Inspect logs in %RUN_LOG%"
goto :fail

:backend_ready
call :log "[STATUS] Health passed"

>> "%STACK_STATE_LOG%" echo.
>> "%STACK_STATE_LOG%" echo ========================================
>> "%STACK_STATE_LOG%" echo [STACK STATUS] %date% %time%
>> "%STACK_STATE_LOG%" echo ========================================
>> "%STACK_STATE_LOG%" echo [COMMAND] docker compose -f docker/docker-compose.yml ps
docker compose -f docker/docker-compose.yml %COMPOSE_PROFILE_ARGS% ps >> "%STACK_STATE_LOG%" 2>&1

tasklist /v | findstr /I /C:"%STACK_LOG_WINDOW_TITLE%" >nul
if errorlevel 1 (
    >> "%STACK_LOG%" echo.
    >> "%STACK_LOG%" echo ========================================
    >> "%STACK_LOG%" echo [STACK LOG SESSION] %date% %time%
    >> "%STACK_LOG%" echo ========================================
    call :log "[INFO] Streaming Docker logs to %STACK_LOG%"
    start "%STACK_LOG_WINDOW_TITLE%" /min cmd /d /c "cd /d "%ROOT%" && docker compose -f docker/docker-compose.yml %COMPOSE_PROFILE_ARGS% logs -f --no-color --tail=300 1>> "%STACK_LOG%" 2>&1"
) else (
    call :log "[INFO] Docker log streamer is already running"
)

if /I "%FRONTEND_MODE%"=="docker" (
    call :log "[INFO] FRONTEND_MODE=docker; using compose frontend at http://localhost"
    for /l %%A in (1,1,%FRONTEND_READY_TIMEOUT_SECONDS%) do (
        curl.exe -fsS "http://127.0.0.1/login.html?api=http://localhost:8000" >nul 2>&1
        if not errorlevel 1 goto :frontend_ready
        timeout /t 1 /nobreak >nul
    )
    call :log "[ERROR] Docker frontend did not become reachable in time."
    goto :fail
)

netstat -ano | findstr /R /C:":%FRONTEND_PORT% .*LISTENING" >nul 2>&1
if errorlevel 1 (
    >> "%FRONTEND_LOG%" echo.
    >> "%FRONTEND_LOG%" echo ========================================
    >> "%FRONTEND_LOG%" echo [FRONTEND LOG SESSION] %date% %time%
    >> "%FRONTEND_LOG%" echo ========================================
    call :log "[INFO] Starting frontend server on http://localhost:%FRONTEND_PORT%"
    call :log "[INFO] Frontend logs: %FRONTEND_LOG%"
    start "%FRONTEND_WINDOW_TITLE%" /min cmd /d /c "cd /d "%ROOT%\frontend" && "%FRONTEND_PYTHON%" -m http.server %FRONTEND_PORT% --bind 127.0.0.1 1>> "%FRONTEND_LOG%" 2>&1"
    for /l %%A in (1,1,20) do (
        curl.exe -fsS "http://127.0.0.1:%FRONTEND_PORT%/" >nul 2>&1
        if not errorlevel 1 goto :frontend_ready
        timeout /t 1 /nobreak >nul
    )
    call :log "[ERROR] Frontend server did not start in time."
    goto :fail
) else (
    call :log "[INFO] Frontend server already listening on port %FRONTEND_PORT%"
    for /l %%A in (1,1,%FRONTEND_READY_TIMEOUT_SECONDS%) do (
        curl.exe -fsS "http://127.0.0.1:%FRONTEND_PORT%/" >nul 2>&1
        if not errorlevel 1 goto :frontend_ready
        timeout /t 1 /nobreak >nul
    )
    call :log "[ERROR] Frontend port is listening, but HTTP readiness failed."
    goto :fail
)

:frontend_ready
call :log "[STATUS] Frontend ready"

if /I "%RUN_SMOKE%"=="1" (
    call :log "[INFO] RUN_SMOKE=1; running tools\test_all.py"
    "%FRONTEND_PYTHON%" tools\test_all.py >> "%RUN_LOG%" 2>&1
    if errorlevel 1 (
        call :log "[STATUS] Smoke failed"
    ) else (
        call :log "[STATUS] Smoke passed"
    )
) else (
    call :log "[STATUS] Smoke not run (set RUN_SMOKE=1 to enable)"
)

call :log "[INFO] Opening frontend..."
start "" "%FRONTEND_URL%" >nul 2>&1

call :log "."
call :log "========================================"
call :log "[✓] RAGMind is running"
call :log "========================================"
call :log "."
call :log "Backend:   http://localhost:8000"
call :log "Frontend:  %FRONTEND_URL%"
call :log "Health:    %BACKEND_HEALTH_URL%"
call :log "Logs:      %RUN_LOG%"
call :log "Stack Log: %STACK_LOG%"
call :log "Stack PS:  %STACK_STATE_LOG%"
call :log "."
call :log "Stop with:"
call :log "  scripts\dev\stop.bat"
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
) else (
    call :log "[HINT] Start Docker Desktop, wait for Engine to become ready, then retry."
)
goto :eof

:log
echo %~1
>> "%RUN_LOG%" echo %~1
goto :eof
