param(
  [ValidateSet("AzureContainerApp", "LocalDocker", "LocalPython")]
  [string]$Mode = "AzureContainerApp",

  [string]$ResourceGroup,
  [string]$ApiAppName = "ragmind-api",
  [string]$DockerContainer = "ragmind-backend"
)

$ErrorActionPreference = "Stop"

switch ($Mode) {
  "AzureContainerApp" {
    if ([string]::IsNullOrWhiteSpace($ResourceGroup)) {
      throw "-ResourceGroup is required when -Mode AzureContainerApp is used."
    }
    if (-not (Get-Command az -ErrorAction SilentlyContinue)) {
      throw "Azure CLI 'az' was not found in PATH."
    }

    az containerapp exec `
      --resource-group $ResourceGroup `
      --name $ApiAppName `
      --command "python -m backend.scripts.sync_telegram_webhooks --json"
    break
  }

  "LocalDocker" {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
      throw "Docker was not found in PATH."
    }
    docker exec -i $DockerContainer python -m backend.scripts.sync_telegram_webhooks --json
    break
  }

  "LocalPython" {
    python -m backend.scripts.sync_telegram_webhooks --json
    break
  }
}
