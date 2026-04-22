@echo off
REM RAGMind Backend Startup Script
setlocal

REM Always run from the script directory.
cd /d "%~dp0"

echo ========================================
echo    RAGMind Backend Server
echo ========================================
echo.

REM Check if Docker services are running
docker ps 2>nul | findstr "ragmind-postgres" >nul
if errorlevel 1 (
    echo [WARNING] Database container is not running!
    echo Starting Docker services...
    set SKIP_DOCKER_PAUSE=1
    call start_docker.bat
    set SKIP_DOCKER_PAUSE=
    if errorlevel 1 (
        echo [ERROR] Failed to start Docker services!
        echo Please run start_docker.bat first or start Docker Desktop.
        pause
        exit /b 1
    )
    echo Waiting for database to be ready...
    timeout /t 5 /nobreak >nul
)
echo [✓] Database is running
echo.

REM Check if RabbitMQ is running
docker ps 2>nul | findstr "rabbitmq" >nul
if errorlevel 1 (
    echo [WARNING] RabbitMQ is not running! Celery tasks will not be processed.
    echo Run start_docker.bat to start all services.
    echo.
) else (
    echo [✓] RabbitMQ is running
)

REM Check if Redis is running
docker ps 2>nul | findstr "redis" >nul
if errorlevel 1 (
    echo [WARNING] Redis is not running! Celery result backend unavailable.
    echo Run start_docker.bat to start all services.
    echo.
) else (
    echo [✓] Redis is running
)
echo.

REM Check if uv is installed
uv --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: uv is not installed!
    echo Please install uv from: https://docs.astral.sh/uv/getting-started/installation/
    pause
    exit /b 1
)

REM Ensure a working virtual environment python is available
set "VENV_DIR=%~dp0venv"
set "VENV_PYTHON=%VENV_DIR%\Scripts\python.exe"
set "VENV_ACTIVATE=%VENV_DIR%\Scripts\activate.bat"
set "VENV_CFG=%VENV_DIR%\pyvenv.cfg"
set "NEED_VENV_CREATE="

if not exist "%VENV_PYTHON%" (
    set "NEED_VENV_CREATE=1"
)

if not exist "%VENV_CFG%" (
    if exist "%VENV_DIR%" (
        echo [WARNING] Existing virtual environment is incomplete. Recreating...
        rmdir /s /q "%VENV_DIR%"
    )
    set "NEED_VENV_CREATE=1"
)

if defined NEED_VENV_CREATE (
    echo Creating virtual environment with uv...
    uv venv "%VENV_DIR%"
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo.
)

if not exist "%VENV_PYTHON%" (
    echo [ERROR] Virtual environment Python executable not found at "%VENV_PYTHON%".
    pause
    exit /b 1
)

if not exist "%VENV_CFG%" (
    echo [ERROR] Virtual environment configuration file not found at "%VENV_CFG%".
    pause
    exit /b 1
)

echo Using Python interpreter:
echo   "%VENV_PYTHON%"

if exist "%VENV_ACTIVATE%" (
    echo Activating virtual environment...
    call "%VENV_ACTIVATE%"
) else (
    echo [WARNING] activate.bat not found. Continuing with direct venv python path.
)
echo.

REM Ensure Celery worker is running (auto-start in a separate terminal)
if not defined SKIP_CELERY_AUTOSTART (
    tasklist /v /fi "imagename eq cmd.exe" | findstr /I "RAGMind Celery Worker" >nul
    if errorlevel 1 (
        echo Starting Celery worker in a separate window...
        start "RAGMind Celery Worker" cmd /k "cd /d \"%~dp0\" && \"%VENV_PYTHON%\" -m celery -A backend.celery_app:celery_app worker -l info -Q default,file_processing -P solo"
        timeout /t 2 /nobreak >nul
    ) else (
        echo [✓] Celery worker window is already running
    )
    echo.
)

REM Install dependencies with uv (much faster!)
echo Installing/Updating dependencies with uv...
uv pip install --python "%VENV_PYTHON%" -r backend\requirements.txt
if errorlevel 1 (
    echo [WARNING] uv install failed. Trying pip fallback...
    "%VENV_PYTHON%" -m pip install -r backend\requirements.txt
    if errorlevel 1 (
        echo [ERROR] Failed to install dependencies.
        pause
        exit /b 1
    )
)
echo.

REM Initialize database
echo Initializing database...
"%VENV_PYTHON%" backend\init_database.py
if errorlevel 1 (
    echo [ERROR] Database initialization failed.
    pause
    exit /b 1
)
echo.

REM Resolve API port from .env, then auto-shift if port is already occupied.
set "API_PORT="
if exist ".env" (
    for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
        if /I "%%A"=="API_PORT" set "API_PORT=%%B"
    )
)
if not defined API_PORT set "API_PORT=8001"
set "API_PORT=%API_PORT: =%"
call :find_free_port API_PORT

REM Resolve frontend port and avoid clashes with existing http.server instances.
set "FRONTEND_PORT=8080"
call :find_free_port FRONTEND_PORT

set "API_BASE_URL=http://127.0.0.1:%API_PORT%"
set "FRONTEND_URL=http://localhost:%FRONTEND_PORT%"
set "CACHE_BUST=%RANDOM%%RANDOM%"

REM Start server
echo Starting FastAPI server...
echo Server will be available at: %API_BASE_URL%
echo API docs at: %API_BASE_URL%/docs
echo.
echo [✓] Celery worker should be running in: "RAGMind Celery Worker" window
echo     (set SKIP_CELERY_AUTOSTART=1 if you want to disable this)
echo.
echo Starting frontend server at: %FRONTEND_URL%
start "RAGMind Frontend" "%VENV_PYTHON%" -m http.server %FRONTEND_PORT% --directory "%~dp0frontend"
echo Opening login page...
start "" "%FRONTEND_URL%/login.html?api=%API_BASE_URL%&cb=%CACHE_BUST%"
"%VENV_PYTHON%" -m uvicorn backend.main:app --host 0.0.0.0 --port %API_PORT%

exit /b %errorlevel%

:find_free_port
setlocal EnableDelayedExpansion
set "PORT_VAR_NAME=%~1"
call set "PORT_VALUE=%%%PORT_VAR_NAME%%%"
if not defined PORT_VALUE set "PORT_VALUE=0"

:find_free_port_loop
netstat -ano | findstr /R /C:":!PORT_VALUE! .*LISTENING" >nul
if not errorlevel 1 (
    set /a NEXT_PORT=!PORT_VALUE!+1
    echo [WARNING] Port !PORT_VALUE! is in use. Trying !NEXT_PORT!...
    set "PORT_VALUE=!NEXT_PORT!"
    goto :find_free_port_loop
)

endlocal & set "%~1=%PORT_VALUE%"
exit /b 0
