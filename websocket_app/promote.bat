@echo off
setlocal enabledelayedexpansion

echo 🚀 Starting Blue/Green Deployment...

REM STEP 1: Decide next color
for /f "tokens=2 delims=_:" %%i in ('findstr /v "^#" nginx\default.conf ^| findstr "server web_"') do (
    set CURRENT_COLOR=%%i
    goto :found_color
)
:found_color

if "%CURRENT_COLOR%"=="blue" (
    set NEXT_COLOR=green
    set NEXT_PORT=8002
) else (
    set NEXT_COLOR=blue
    set NEXT_PORT=8001
)

echo 🔄 Current: %CURRENT_COLOR%, Next: %NEXT_COLOR%

REM STEP 2: Build and start next color
echo 🏗️  Building and starting web_%NEXT_COLOR%...
docker-compose up -d --build web_%NEXT_COLOR%
if errorlevel 1 (
    echo ❌ Failed to start web_%NEXT_COLOR%
    exit /b 1
)

REM STEP 3: Wait for health check
echo ⏳ Waiting for health check...
set MAX_ATTEMPTS=30
set ATTEMPT=0

:health_check_loop
set /a ATTEMPT+=1
echo ⏳ Attempt %ATTEMPT%/%MAX_ATTEMPTS% - waiting for %NEXT_COLOR% to be ready...

curl -f "http://localhost:%NEXT_PORT%/health/" >nul 2>&1
if errorlevel 1 (
    if %ATTEMPT% geq %MAX_ATTEMPTS% (
        echo ❌ Health check failed for %NEXT_COLOR% after %MAX_ATTEMPTS% attempts
        exit /b 1
    )
    timeout /t 2 /nobreak >nul
    goto :health_check_loop
)

echo ✅ Health check passed for %NEXT_COLOR%

REM STEP 4: Flip traffic
echo 🔁 Switching NGINX traffic to %NEXT_COLOR%
powershell -Command "(Get-Content nginx\default.conf) -replace 'server web_%CURRENT_COLOR%', 'server web_%NEXT_COLOR%' | Set-Content nginx\default.conf"
docker-compose restart nginx
if errorlevel 1 (
    echo ❌ Failed to restart nginx
    exit /b 1
)

REM Wait for nginx to restart
timeout /t 3 /nobreak >nul

REM STEP 5: Test the switch
echo 🧪 Testing traffic switch...
curl -f "http://localhost/health/" >nul 2>&1
if errorlevel 1 (
    echo ❌ Traffic switch failed, rolling back...
    powershell -Command "(Get-Content nginx\default.conf) -replace 'server web_%NEXT_COLOR%', 'server web_%CURRENT_COLOR%' | Set-Content nginx\default.conf"
    docker-compose restart nginx
    exit /b 1
)
echo ✅ Traffic successfully switched to %NEXT_COLOR%

REM STEP 6: Stop old container
echo 🧹 Gracefully stopping old container: web_%CURRENT_COLOR%
docker-compose stop web_%CURRENT_COLOR%

echo 🎉 Blue/Green promotion to %NEXT_COLOR% completed successfully!
echo 🌐 Application is now running on: http://localhost