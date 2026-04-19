param(
    [string[]]$HealthUrls = @(
        "http://127.0.0.1:8001/health",
        "http://127.0.0.1:8000/health"
    ),
    [string]$LoginUrl = "http://localhost:8080/login.html",
    [int]$MaxAttempts = 120,
    [int]$DelayMilliseconds = 500
)

$opened = $false

for ($i = 0; $i -lt $MaxAttempts; $i++) {
    foreach ($healthUrl in $HealthUrls) {
        try {
            $null = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 2
            Start-Process $LoginUrl
            $opened = $true
            break
        }
        catch {
            # Continue trying other health endpoints.
        }
    }

    if ($opened) {
        break
    }

    Start-Sleep -Milliseconds $DelayMilliseconds
}

# Fallback: still open login page so user can inspect UI even if health check never passed.
if (-not $opened) {
    Start-Process $LoginUrl
}
