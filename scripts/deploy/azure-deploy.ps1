param(
  [Parameter(Mandatory = $true)]
  [string]$ResourceGroup,

  [Parameter(Mandatory = $true)]
  [string]$RootDomain,

  [string]$Location = "westeurope",
  [string]$NamePrefix = "ragmind",
  [string]$ImageTag = (Get-Date -Format "yyyyMMddHHmmss"),
  [string]$PlatformOwnerUsername = $env:PLATFORM_OWNER_USERNAME,
  [switch]$BindCustomDomains,
  [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

function Require-Command {
  param([string]$Name)
  if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
    throw "Required command '$Name' was not found in PATH."
  }
}

function Require-Env {
  param([string]$Name)
  $value = [Environment]::GetEnvironmentVariable($Name)
  if ([string]::IsNullOrWhiteSpace($value)) {
    throw "Required environment variable '$Name' is not set."
  }
  return $value
}

function New-ParameterFile {
  param(
    [string]$ApiImage,
    [string]$WebImage
  )

  $platformOwnerValue = ""
  if (-not [string]::IsNullOrWhiteSpace($PlatformOwnerUsername)) {
    $platformOwnerValue = $PlatformOwnerUsername
  }

  $parameters = [ordered]@{
    '$schema' = "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#"
    contentVersion = "1.0.0.0"
    parameters = [ordered]@{
      namePrefix = @{ value = $NamePrefix }
      location = @{ value = $Location }
      rootDomain = @{ value = $RootDomain }
      apiImage = @{ value = $ApiImage }
      webImage = @{ value = $WebImage }
      postgresAdminLogin = @{ value = "ragmindadmin" }
      postgresAdminPassword = @{ value = (Require-Env "AZURE_POSTGRES_ADMIN_PASSWORD") }
      authJwtSecretKey = @{ value = (Require-Env "AUTH_JWT_SECRET_KEY") }
      authAdminPassword = @{ value = (Require-Env "AUTH_ADMIN_PASSWORD") }
      botTokenEncryptionKey = @{ value = (Require-Env "BOT_TOKEN_ENCRYPTION_KEY") }
      groqApiKey = @{ value = (Require-Env "GROQ_API_KEY") }
      cohereApiKey = @{ value = (Require-Env "COHERE_API_KEY") }
      platformOwnerUsername = @{ value = $platformOwnerValue }
      llmProvider = @{ value = "groq-llama-3.3-70b-versatile" }
      embeddingProvider = @{ value = "cohere" }
      answerMaxTokens = @{ value = 1024 }
      apiMaxReplicas = @{ value = 3 }
      workerMaxReplicas = @{ value = 3 }
    }
  }

  $path = Join-Path ([System.IO.Path]::GetTempPath()) ("ragmind-azure-params-{0}.json" -f ([guid]::NewGuid()))
  $parameters | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $path -Encoding UTF8
  return $path
}

function Deploy-Bicep {
  param(
    [string]$ApiImage,
    [string]$WebImage
  )

  $paramFile = New-ParameterFile -ApiImage $ApiImage -WebImage $WebImage
  try {
    $deployment = az deployment group create `
      --resource-group $ResourceGroup `
      --template-file "infra/azure/main.bicep" `
      --parameters "@$paramFile" `
      --query "properties.outputs" `
      --output json | ConvertFrom-Json
    return $deployment
  }
  finally {
    Remove-Item -LiteralPath $paramFile -Force -ErrorAction SilentlyContinue
  }
}

function Wait-HttpOk {
  param(
    [string]$Url,
    [int]$Attempts = 18,
    [int]$DelaySeconds = 10
  )

  for ($i = 1; $i -le $Attempts; $i++) {
    try {
      $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 20
      if ($response.StatusCode -ge 200 -and $response.StatusCode -lt 300) {
        return $true
      }
    }
    catch {
      Write-Host "Waiting for $Url ($i/$Attempts): $($_.Exception.Message)"
    }
    Start-Sleep -Seconds $DelaySeconds
  }
  return $false
}

function New-ManagedCertificateName {
  param(
    [string]$AppName,
    [string]$HostName
  )

  $safeHostName = ($HostName -replace '[^A-Za-z0-9-]', '-').ToLowerInvariant()
  $rawName = ("mc-{0}-{1}" -f $AppName, $safeHostName).ToLowerInvariant().Trim("-")
  if ($rawName.Length -le 63) {
    return $rawName
  }

  $sha256 = [System.Security.Cryptography.SHA256]::Create()
  try {
    $hashBytes = $sha256.ComputeHash([System.Text.Encoding]::UTF8.GetBytes($rawName))
    $hash = ([BitConverter]::ToString($hashBytes)).Replace("-", "").Substring(0, 8).ToLowerInvariant()
  }
  finally {
    $sha256.Dispose()
  }

  return ("{0}-{1}" -f $rawName.Substring(0, 54).Trim("-"), $hash)
}

function Try-BindHostName {
  param(
    [string]$AppName,
    [string]$HostName,
    [string]$DefaultFqdn,
    [string]$EnvironmentName
  )

  Write-Host "Binding $HostName to $AppName..."
  Write-Host "DNS prerequisite: create CNAME $HostName -> $DefaultFqdn before running with -BindCustomDomains."
  Write-Host "If Azure requests domain ownership validation, add the TXT record it prints for asuid.$HostName."

  try {
    try {
      az containerapp hostname add `
        --resource-group $ResourceGroup `
        --name $AppName `
        --hostname $HostName `
        --output none
    }
    catch {
      Write-Warning "Hostname add did not complete for $HostName. Continuing in case it already exists. $($_.Exception.Message)"
    }

    $certificateId = az containerapp env certificate list `
      --resource-group $ResourceGroup `
      --name $EnvironmentName `
      --managed-certificates-only `
      --query "[?properties.subjectName=='$HostName'].id | [0]" `
      --output tsv

    if ([string]::IsNullOrWhiteSpace($certificateId)) {
      $certificateName = New-ManagedCertificateName -AppName $AppName -HostName $HostName
      $certificateId = az containerapp env certificate create `
        --resource-group $ResourceGroup `
        --name $EnvironmentName `
        --certificate-name $certificateName `
        --hostname $HostName `
        --validation-method CNAME `
        --query "id" `
        --output tsv
    }

    az containerapp hostname bind `
      --resource-group $ResourceGroup `
      --name $AppName `
      --hostname $HostName `
      --environment $EnvironmentName `
      --certificate $certificateId `
      --validation-method CNAME `
      --output none
  }
  catch {
    Write-Warning "Custom domain binding failed for $HostName. Configure the CNAME record and rerun with -BindCustomDomains. $($_.Exception.Message)"
  }
}

Require-Command "az"
Require-Command "docker"

az group create --name $ResourceGroup --location $Location --output none

$placeholderImage = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
Write-Host "Deploying Azure resources and placeholder Container Apps..."
$initialOutputs = Deploy-Bicep -ApiImage $placeholderImage -WebImage $placeholderImage

$acrLoginServer = $initialOutputs.acrLoginServer.value
$apiAppName = $initialOutputs.apiAppName.value
$webAppName = $initialOutputs.webAppName.value
$containerAppEnvironmentName = $initialOutputs.containerAppEnvironmentName.value
$apiDefaultFqdn = $initialOutputs.apiDefaultFqdn.value
$webDefaultFqdn = $initialOutputs.webDefaultFqdn.value
$apiCustomHostName = $initialOutputs.apiCustomHostName.value
$webCustomHostName = $initialOutputs.webCustomHostName.value

$apiImage = "$acrLoginServer/ragmind-api:$ImageTag"
$webImage = "$acrLoginServer/ragmind-web:$ImageTag"

if (-not $SkipBuild) {
  $acrName = $acrLoginServer.Split(".")[0]
  az acr login --name $acrName --output none

  Write-Host "Building backend image $apiImage..."
  docker build -f docker/backend.Dockerfile -t $apiImage .
  docker push $apiImage

  Write-Host "Building frontend image $webImage..."
  docker build `
    -f frontend-next/Dockerfile `
    --build-arg "NEXT_PUBLIC_API_BASE_URL=https://$apiCustomHostName" `
    -t $webImage .
  docker push $webImage
}

Write-Host "Deploying Container Apps with production images..."
$finalOutputs = Deploy-Bicep -ApiImage $apiImage -WebImage $webImage

$apiDefaultUrl = "https://$($finalOutputs.apiDefaultFqdn.value)"
$webDefaultUrl = "https://$($finalOutputs.webDefaultFqdn.value)"

if ($BindCustomDomains) {
  Try-BindHostName -AppName $apiAppName -HostName $apiCustomHostName -DefaultFqdn $apiDefaultFqdn -EnvironmentName $containerAppEnvironmentName
  Try-BindHostName -AppName $webAppName -HostName $webCustomHostName -DefaultFqdn $webDefaultFqdn -EnvironmentName $containerAppEnvironmentName
}

Write-Host "Checking API liveness on default Container Apps hostname..."
if (-not (Wait-HttpOk "$apiDefaultUrl/health/live")) {
  throw "API liveness check failed at $apiDefaultUrl/health/live"
}

Write-Host "Checking API readiness on default Container Apps hostname..."
if (-not (Wait-HttpOk "$apiDefaultUrl/health/full" -Attempts 12 -DelaySeconds 10)) {
  throw "API readiness check failed at $apiDefaultUrl/health/full"
}

Write-Host "Checking frontend on default Container Apps hostname..."
if (-not (Wait-HttpOk "$webDefaultUrl/login" -Attempts 12 -DelaySeconds 10)) {
  throw "Frontend check failed at $webDefaultUrl/login"
}

if ($BindCustomDomains) {
  Write-Host "Running Telegram webhook sync through the API container..."
  & "$PSScriptRoot/sync-telegram-webhooks.ps1" `
    -Mode AzureContainerApp `
    -ResourceGroup $ResourceGroup `
    -ApiAppName $apiAppName
}
else {
  Write-Warning "Custom domains were not bound. Telegram webhooks are configured for https://$apiCustomHostName and should be synced only after DNS/custom domain binding succeeds."
}

Write-Host ""
Write-Host "Deployment complete."
Write-Host "API default URL: $apiDefaultUrl"
Write-Host "Web default URL: $webDefaultUrl"
Write-Host "Production API URL: https://$apiCustomHostName"
Write-Host "Production web URL: https://$webCustomHostName"
