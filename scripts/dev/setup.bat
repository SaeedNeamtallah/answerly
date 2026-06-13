@echo off
REM RAGMind Unified Setup Script
setlocal
set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..\..") do set "ROOT=%%~fI"
pushd "%ROOT%"
set "LOGS_DIR=%ROOT%\uploads\logs"
set "RUN_LOG=%LOGS_DIR%\setup.log"
set "HAS_UV=0"
rem Auto-detect virtual environment directory (prefer .venv if it exists, otherwise venv)
set "VENV_DIR=venv"
if exist ".venv\Scripts\python.exe" (
    set "VENV_DIR=.venv"
) else if exist "venv\Scripts\python.exe" (
    set "VENV_DIR=venv"
)
set "VENV_PY=%VENV_DIR%\Scripts\python.exe"
set "COMPOSE_CMD="
set "VENV_CREATE_CMD="
set "VENV_CREATE_LOG_CMD="

if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%"
>> "%RUN_LOG%" echo.
>> "%RUN_LOG%" echo ========================================
>> "%RUN_LOG%" echo [SETUP] %date% %time%
>> "%RUN_LOG%" echo ========================================

call :log "========================================"
call :log "   RAGMind - Setup"
call :log "========================================"
call :log "."

uv --version >nul 2>&1
if errorlevel 1 (
    call :log "[INFO] uv not found in PATH. Falling back to standard Python tooling."
) else (
    set "HAS_UV=1"
    call :log "[INFO] Detected uv in PATH."
)

if exist "%VENV_PY%" (
    "%VENV_PY%" --version >nul 2>&1
    if errorlevel 1 (
        call :log "[WARNING] Existing venv is broken. Recreating it..."
        if exist "%VENV_DIR%" rmdir /s /q "%VENV_DIR%" >> "%RUN_LOG%" 2>&1
    )
)

if exist "%VENV_PY%" goto :venv_ready

call :prepare_venv_command
if errorlevel 1 goto :fail

call :log "[INFO] Creating virtual environment..."
>> "%RUN_LOG%" echo [COMMAND] %VENV_CREATE_LOG_CMD%
call %VENV_CREATE_CMD% >> "%RUN_LOG%" 2>&1
if not errorlevel 1 goto :venv_created

if "%HAS_UV%"=="1" (
    call :log "[WARNING] uv could not create a Python 3.11 venv. Retrying with default Python..."
    >> "%RUN_LOG%" echo [COMMAND] uv venv %VENV_DIR%
    uv venv %VENV_DIR% >> "%RUN_LOG%" 2>&1
)
if errorlevel 1 (
    call :log "[ERROR] Failed to create the virtual environment."
    goto :fail
)

:venv_created
:venv_ready

"%VENV_PY%" --version >nul 2>&1
if errorlevel 1 (
    call :log "[ERROR] Virtual environment Python is not runnable."
    goto :fail
)

call :log "[INFO] Installing Python dependencies..."
if "%HAS_UV%"=="1" (
    >> "%RUN_LOG%" echo [COMMAND] uv pip install --python "%VENV_PY%" -r backend\requirements.txt
    uv pip install --python "%VENV_PY%" -r backend\requirements.txt >> "%RUN_LOG%" 2>&1
    if errorlevel 1 (
        call :log "[WARNING] uv pip install failed. Retrying with pip..."
        >> "%RUN_LOG%" echo [COMMAND] "%VENV_PY%" -m pip install -r backend\requirements.txt
        "%VENV_PY%" -m pip install -r backend\requirements.txt >> "%RUN_LOG%" 2>&1
    )
) else (
    >> "%RUN_LOG%" echo [COMMAND] "%VENV_PY%" -m pip install -r backend\requirements.txt
    "%VENV_PY%" -m pip install -r backend\requirements.txt >> "%RUN_LOG%" 2>&1
)
if errorlevel 1 (
    call :log "[ERROR] Failed to install Python dependencies using uv/pip."
    goto :fail
)

if not exist ".env" (
    if exist ".env.example" (
        call :log "[INFO] Creating .env from .env.example..."
        copy /Y .env.example .env >> "%RUN_LOG%" 2>&1
    ) else (
        call :log "[WARNING] .env.example not found. Create .env manually before start."
    )
) else (
    call :log "[INFO] Existing .env detected. Keeping it unchanged."
)

if not exist "uploads" (
    mkdir uploads >> "%RUN_LOG%" 2>&1
    call :log "[INFO] Created uploads directory."
)
if not exist "tmp" (
    mkdir tmp >> "%RUN_LOG%" 2>&1
    call :log "[INFO] Created tmp directory."
)
if not exist "%LOGS_DIR%" mkdir "%LOGS_DIR%" >> "%RUN_LOG%" 2>&1

docker --version >nul 2>&1
if errorlevel 1 (
    call :log "[WARNING] Docker is not available in PATH."
    call :log "Setup completed for Python-side tooling only."
    call :log "Install Docker Desktop before running scripts\dev\start.bat"
    goto :done
)

call :detect_compose
if errorlevel 1 (
    call :log "[WARNING] Docker was found, but Compose command was not found."
    call :log "Install Docker Desktop (Compose plugin) or docker-compose."
    goto :done
)

set "DOCKER_INFO_TMP=%TEMP%\ragmind_docker_info_%RANDOM%.log"
docker info > "%DOCKER_INFO_TMP%" 2>&1
if errorlevel 1 (
    call :log "[WARNING] Docker Desktop is installed but not ready."
    call :log "Start Docker Desktop before running scripts\dev\start.bat"
    call :docker_info_hint "%DOCKER_INFO_TMP%"
    del "%DOCKER_INFO_TMP%" >nul 2>&1
    goto :done
)
del "%DOCKER_INFO_TMP%" >nul 2>&1

call :log "[INFO] Docker is available. Validating compose file using '%COMPOSE_CMD%'..."
>> "%RUN_LOG%" echo [COMMAND] %COMPOSE_CMD% -f docker/docker-compose.yml config
%COMPOSE_CMD% -f docker/docker-compose.yml config >> "%RUN_LOG%" 2>&1
if errorlevel 1 (
    call :log "[ERROR] docker-compose.yml validation failed."
    goto :fail
)

call :log "[INFO] Setup finished successfully."
call :log "."
call :log "Next steps:"
call :log "  1. Review .env"
call :log "  2. Run scripts\dev\start.bat"
call :log "  3. Stop with scripts\dev\stop.bat"
call :log "  4. Python in venv: %VENV_PY%"
call :log "  5. Setup log: %RUN_LOG%"
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
    call :log "[HINT] Start Docker Desktop and wait until Engine is ready, then rerun setup/start."
)
goto :eof

:prepare_venv_command
if "%HAS_UV%"=="1" (
    set "VENV_CREATE_CMD=uv venv --python 3.11 %VENV_DIR%"
    set "VENV_CREATE_LOG_CMD=uv venv --python 3.11 %VENV_DIR%"
    goto :eof
)

py -3.11 --version >nul 2>&1
if not errorlevel 1 (
    set "VENV_CREATE_CMD=py -3.11 -m venv %VENV_DIR%"
    set "VENV_CREATE_LOG_CMD=py -3.11 -m venv %VENV_DIR%"
    goto :eof
)

py -3 --version >nul 2>&1
if not errorlevel 1 (
    set "VENV_CREATE_CMD=py -3 -m venv %VENV_DIR%"
    set "VENV_CREATE_LOG_CMD=py -3 -m venv %VENV_DIR%"
    goto :eof
)

python --version >nul 2>&1
if not errorlevel 1 (
    set "VENV_CREATE_CMD=python -m venv %VENV_DIR%"
    set "VENV_CREATE_LOG_CMD=python -m venv %VENV_DIR%"
    goto :eof
)

call :log "[ERROR] No suitable Python runtime was found to create venv."
call :log "Install Python 3.11+ (or install uv) and ensure it is available in PATH."
exit /b 1

:detect_compose
docker compose version >nul 2>&1
if not errorlevel 1 (
    set "COMPOSE_CMD=docker compose"
    goto :eof
)
docker-compose --version >nul 2>&1
if not errorlevel 1 (
    set "COMPOSE_CMD=docker-compose"
    goto :eof
)
exit /b 1

:log
echo %~1
>> "%RUN_LOG%" echo %~1
goto :eof
