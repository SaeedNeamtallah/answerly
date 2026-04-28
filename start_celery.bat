@echo off
REM RAGMind Celery Worker Startup Script

echo ========================================
echo    RAGMind - Celery Worker
echo ========================================
echo.

REM Check if Docker services are running (RabbitMQ)
docker ps 2>nul | findstr "rabbitmq" >nul
if errorlevel 1 (
    echo [WARNING] RabbitMQ container is not running!
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
    echo Waiting for RabbitMQ and Redis to be ready...
    timeout /t 10 /nobreak >nul
)
echo [✓] RabbitMQ is running
echo.

REM Check if Redis is running
docker ps 2>nul | findstr "redis" >nul
if errorlevel 1 (
    echo [WARNING] Redis container is not running!
    echo Please run start_docker.bat first.
    pause
    exit /b 1
)
echo [✓] Redis is running
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo [ERROR] Virtual environment not found!
    echo Please run setup.bat or start_backend.bat first.
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Start Celery worker
echo Starting Celery worker...
echo Listening on queues: default, file_processing
echo.
echo Press Ctrl+C to stop the worker.
echo ========================================
echo.
celery -A backend.celery_app:celery_app worker -l info -Q default,file_processing -P solo
