@echo off
REM RAGMind Docker Services Startup Script

echo ========================================
echo    RAGMind - Docker Services
echo ========================================
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not installed!
    echo Please install Docker Desktop from: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [✓] Docker is running
echo.

REM Start services
echo Starting PostgreSQL, Qdrant, RabbitMQ and Redis containers...
docker compose -f docker/docker-compose.yml up -d

if errorlevel 1 (
    echo [ERROR] Failed to start Docker services!
    pause
    exit /b 1
)

echo.
echo ========================================
echo [✓] Docker services started successfully!
echo ========================================
echo.
echo Services running:
echo   - PostgreSQL:          localhost:5435
echo   - Qdrant:              localhost:6381
echo   - RabbitMQ:            localhost:5729  (Management: localhost:15672)
echo   - Redis:               localhost:6383
echo.
echo To stop services: stop_docker.bat
echo To view logs: docker compose -f docker/docker-compose.yml logs -f
echo.
if not defined SKIP_DOCKER_PAUSE (
    pause
)
