# Azure Deployment

This folder contains the Bicep deployment for the production Telegram SaaS webhook path.

## Resources

- Azure Container Registry
- Azure Container Apps environment
- `ragmind-api` external Container App
- `ragmind-web` external Container App
- `ragmind-worker` internal Container App
- `ragmind-scheduler` internal Container App
- Azure Database for PostgreSQL Flexible Server with `VECTOR` allow-listed
- Azure Managed Redis over TLS
- Azure Files share mounted at `/app/uploads`
- Log Analytics workspace

## Deploy

Run from the repository root:

```powershell
$env:AZURE_POSTGRES_ADMIN_PASSWORD = "<strong password>"
$env:AUTH_JWT_SECRET_KEY = "<32+ char signing key>"
$env:AUTH_ADMIN_PASSWORD = "<strong admin password>"
$env:BOT_TOKEN_ENCRYPTION_KEY = "<Fernet key>"
$env:GROQ_API_KEY = "<Groq key>"
$env:COHERE_API_KEY = "<Cohere key>"

scripts\deploy\azure-deploy.ps1 -ResourceGroup ragmind-prod-rg -RootDomain example.com
```

Omit `-RootDomain` to deploy with the default Azure Container Apps HTTPS hostnames. In that mode the script feeds those default URLs back into the API, frontend, CORS, and Telegram webhook base URL.
If the app region does not support Azure Managed Redis, keep the app region and pass `-RedisLocation <region>` for a supported Redis region.

Create DNS CNAME records before binding custom domains:

- `api.example.com` -> API default Container Apps hostname printed by the script
- `app.example.com` -> web default Container Apps hostname printed by the script

Then bind custom domains and synchronize Telegram webhooks. The script adds the hostnames, creates or reuses Azure Container Apps managed certificates, and binds them. If Azure prints a domain ownership TXT challenge, add the `asuid.*` record it prints and rerun the same command.

```powershell
scripts\deploy\azure-deploy.ps1 -ResourceGroup ragmind-prod-rg -RootDomain example.com -BindCustomDomains
scripts\deploy\sync-telegram-webhooks.ps1 -Mode AzureContainerApp -ResourceGroup ragmind-prod-rg -ApiAppName ragmind-api
```

## Validate

```powershell
Invoke-RestMethod https://api.example.com/health/live
Invoke-RestMethod https://api.example.com/health/full
Invoke-WebRequest https://app.example.com/login
```

For Telegram, `getWebhookInfo` should report the `api.example.com` webhook URL, `pending_update_count=0`, and no `last_error_message`.
