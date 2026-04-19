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

REM Ensure Docker env files exist (required by docker-compose.yml)
if not exist "docker\env\" (
    echo [INFO] Creating docker\env directory...
    mkdir "docker\env" >nul 2>&1
)

if not exist "docker\env\.env.rabbitmq" (
    echo [INFO] Creating docker\env\.env.rabbitmq...
    (
        echo RABBITMQ_DEFAULT_USER=minirag_user
        echo RABBITMQ_DEFAULT_PASS=minirag_rabbitmq_2222
        echo RABBITMQ_DEFAULT_VHOST=minirag_vhost
    ) > "docker\env\.env.rabbitmq"
)

if not exist "docker\env\.env.redis" (
    echo [INFO] Creating docker\env\.env.redis...
    (
        echo REDIS_PASSWORD=minirag_redis_2222
    ) > "docker\env\.env.redis"
)

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
