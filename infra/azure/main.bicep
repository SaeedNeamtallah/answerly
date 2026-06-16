targetScope = 'resourceGroup'

@description('Short lowercase deployment prefix used in resource names.')
param namePrefix string = 'ragmind'

@description('Azure region for all resources.')
param location string = 'westeurope'

@description('Owned production root domain. The deployment uses api.<rootDomain> and app.<rootDomain>.')
param rootDomain string

@description('Backend image to run after it has been pushed to ACR.')
param apiImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('Frontend image to run after it has been pushed to ACR.')
param webImage string = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

@description('PostgreSQL administrator username.')
param postgresAdminLogin string = 'ragmindadmin'

@secure()
@description('PostgreSQL administrator password.')
param postgresAdminPassword string

@secure()
@description('Strong JWT signing key for production.')
param authJwtSecretKey string

@secure()
@description('Platform admin password for production bootstrap/login.')
param authAdminPassword string

@secure()
@description('Fernet key used to encrypt Telegram bot tokens.')
param botTokenEncryptionKey string

@secure()
@description('Groq API key used by the default production LLM provider.')
param groqApiKey string

@secure()
@description('Cohere API key used by the default production embedding provider.')
param cohereApiKey string

@description('Platform owner username promoted after login.')
param platformOwnerUsername string = ''

@description('Default LLM provider for production runtime config/env.')
param llmProvider string = 'groq-llama-3.3-70b-versatile'

@description('Default embedding provider for production runtime config/env.')
param embeddingProvider string = 'cohere'

@description('Default answer max token cap.')
param answerMaxTokens int = 1024

@description('Maximum API replicas.')
param apiMaxReplicas int = 3

@description('Maximum worker replicas.')
param workerMaxReplicas int = 3

var normalizedPrefix = toLower(replace(namePrefix, '_', '-'))
var uniqueSuffix = uniqueString(resourceGroup().id, normalizedPrefix)
var apiHostName = 'api.${rootDomain}'
var webHostName = 'app.${rootDomain}'
var acrName = take(toLower(replace('${normalizedPrefix}${uniqueSuffix}acr', '-', '')), 50)
var storageName = take(toLower(replace('${normalizedPrefix}${uniqueSuffix}st', '-', '')), 24)
var environmentName = '${normalizedPrefix}-aca-env'
var logAnalyticsName = '${normalizedPrefix}-logs'
var postgresName = '${normalizedPrefix}-pg-${uniqueSuffix}'
var postgresDatabaseName = 'ragmind'
var redisName = '${normalizedPrefix}-redis-${uniqueSuffix}'
var apiAppName = '${normalizedPrefix}-api'
var workerAppName = '${normalizedPrefix}-worker'
var schedulerAppName = '${normalizedPrefix}-scheduler'
var webAppName = '${normalizedPrefix}-web'
var uploadsShareName = 'uploads'

resource logs 'Microsoft.OperationalInsights/workspaces@2023-09-01' = {
  name: logAnalyticsName
  location: location
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource registry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: acrName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
  }
}

resource fileService 'Microsoft.Storage/storageAccounts/fileServices@2023-05-01' = {
  parent: storage
  name: 'default'
}

resource uploadsShare 'Microsoft.Storage/storageAccounts/fileServices/shares@2023-05-01' = {
  parent: fileService
  name: uploadsShareName
  properties: {
    shareQuota: 100
  }
}

resource postgres 'Microsoft.DBforPostgreSQL/flexibleServers@2023-12-01-preview' = {
  name: postgresName
  location: location
  sku: {
    name: 'Standard_B1ms'
    tier: 'Burstable'
  }
  properties: {
    version: '16'
    administratorLogin: postgresAdminLogin
    administratorLoginPassword: postgresAdminPassword
    storage: {
      storageSizeGB: 32
    }
    backup: {
      backupRetentionDays: 7
      geoRedundantBackup: 'Disabled'
    }
    highAvailability: {
      mode: 'Disabled'
    }
    network: {
      publicNetworkAccess: 'Enabled'
    }
  }
}

resource postgresDatabase 'Microsoft.DBforPostgreSQL/flexibleServers/databases@2023-12-01-preview' = {
  parent: postgres
  name: postgresDatabaseName
  properties: {
    charset: 'UTF8'
    collation: 'en_US.utf8'
  }
}

resource postgresAllowAzure 'Microsoft.DBforPostgreSQL/flexibleServers/firewallRules@2023-12-01-preview' = {
  parent: postgres
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

resource postgresVectorExtension 'Microsoft.DBforPostgreSQL/flexibleServers/configurations@2023-12-01-preview' = {
  parent: postgres
  name: 'azure.extensions'
  properties: {
    value: 'VECTOR'
    source: 'user-override'
  }
}

resource redis 'Microsoft.Cache/Redis@2024-11-01' = {
  name: redisName
  location: location
  properties: {
    sku: {
      name: 'Basic'
      family: 'C'
      capacity: 0
    }
    enableNonSslPort: false
    minimumTlsVersion: '1.2'
  }
}

resource acaEnvironment 'Microsoft.App/managedEnvironments@2024-03-01' = {
  name: environmentName
  location: location
  properties: {
    appLogsConfiguration: {
      destination: 'log-analytics'
      logAnalyticsConfiguration: {
        customerId: logs.properties.customerId
        sharedKey: logs.listKeys().primarySharedKey
      }
    }
  }
}

resource uploadsMount 'Microsoft.App/managedEnvironments/storages@2024-03-01' = {
  parent: acaEnvironment
  name: 'uploads'
  properties: {
    azureFile: {
      accountName: storage.name
      accountKey: storage.listKeys().keys[0].value
      shareName: uploadsShare.name
      accessMode: 'ReadWrite'
    }
  }
}

var acrCredentials = registry.listCredentials()
var redisKey = redis.listKeys().primaryKey
var databaseUrl = 'postgresql+asyncpg://${postgresAdminLogin}:${uriComponent(postgresAdminPassword)}@${postgres.properties.fullyQualifiedDomainName}:5432/${postgresDatabaseName}?ssl=require'
var redisCeleryUrl = 'rediss://:${uriComponent(redisKey)}@${redis.properties.hostName}:6380/0?ssl_cert_reqs=required'
var corsOrigins = '["https://${webHostName}"]'
var publicWebhookBaseUrl = 'https://${apiHostName}'

var backendSecrets = [
  {
    name: 'acr-password'
    value: acrCredentials.passwords[0].value
  }
  {
    name: 'database-url'
    value: databaseUrl
  }
  {
    name: 'celery-broker-url'
    value: redisCeleryUrl
  }
  {
    name: 'celery-result-backend'
    value: redisCeleryUrl
  }
  {
    name: 'auth-jwt-secret-key'
    value: authJwtSecretKey
  }
  {
    name: 'auth-admin-password'
    value: authAdminPassword
  }
  {
    name: 'bot-token-encryption-key'
    value: botTokenEncryptionKey
  }
  {
    name: 'groq-api-key'
    value: groqApiKey
  }
  {
    name: 'cohere-api-key'
    value: cohereApiKey
  }
]

var commonBackendEnv = [
  {
    name: 'ENVIRONMENT'
    value: 'production'
  }
  {
    name: 'DATABASE_URL'
    secretRef: 'database-url'
  }
  {
    name: 'CELERY_BROKER_URL'
    secretRef: 'celery-broker-url'
  }
  {
    name: 'CELERY_RESULT_BACKEND'
    secretRef: 'celery-result-backend'
  }
  {
    name: 'AUTH_JWT_SECRET_KEY'
    secretRef: 'auth-jwt-secret-key'
  }
  {
    name: 'AUTH_ADMIN_PASSWORD'
    secretRef: 'auth-admin-password'
  }
  {
    name: 'BOT_TOKEN_ENCRYPTION_KEY'
    secretRef: 'bot-token-encryption-key'
  }
  {
    name: 'GROQ_API_KEY'
    secretRef: 'groq-api-key'
  }
  {
    name: 'COHERE_API_KEY'
    secretRef: 'cohere-api-key'
  }
  {
    name: 'LLM_PROVIDER'
    value: llmProvider
  }
  {
    name: 'EMBEDDING_PROVIDER'
    value: embeddingProvider
  }
  {
    name: 'VECTOR_DB_PROVIDER'
    value: 'pgvector'
  }
  {
    name: 'PUBLIC_WEBHOOK_BASE_URL'
    value: publicWebhookBaseUrl
  }
  {
    name: 'TELEGRAM_WEBHOOK_REQUIRE_SECRET_HEADER'
    value: 'true'
  }
  {
    name: 'TELEGRAM_RATE_LIMIT_REDIS_URL'
    secretRef: 'celery-result-backend'
  }
  {
    name: 'CORS_ORIGINS'
    value: corsOrigins
  }
  {
    name: 'ANSWER_MAX_TOKENS'
    value: string(answerMaxTokens)
  }
  {
    name: 'RAGMIND_SHARED_CONFIG_DIR'
    value: '/app/uploads/config'
  }
  {
    name: 'UPLOAD_DIR'
    value: '/app/uploads'
  }
  {
    name: 'PLATFORM_OWNER_USERNAME'
    value: platformOwnerUsername
  }
  {
    name: 'TELEGRAM_OUTBOX_POLL_INTERVAL_SECONDS'
    value: '2'
  }
  {
    name: 'TELEGRAM_OUTBOX_MAX_DELIVERY_ATTEMPTS'
    value: '3'
  }
  {
    name: 'TELEGRAM_OUTBOX_CLAIM_TIMEOUT_SECONDS'
    value: '120'
  }
  {
    name: 'TELEGRAM_OUTBOX_RETRY_BASE_SECONDS'
    value: '30'
  }
  {
    name: 'TELEGRAM_OUTBOX_RETRY_MAX_SECONDS'
    value: '900'
  }
  {
    name: 'TELEGRAM_RAW_PAYLOAD_CLEANUP_INTERVAL_SECONDS'
    value: '21600'
  }
  {
    name: 'TELEGRAM_REPLY_GENERATION_CLAIM_TIMEOUT_SECONDS'
    value: '600'
  }
  {
    name: 'PROMETHEUS_BASE_URL'
    value: ''
  }
  {
    name: 'GRAFANA_PUBLIC_URL'
    value: ''
  }
  {
    name: 'GRAFANA_INTERNAL_URL'
    value: ''
  }
  {
    name: 'GRAFANA_EMBED_ENABLED'
    value: 'false'
  }
]

resource apiApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: apiAppName
  location: location
  properties: {
    managedEnvironmentId: acaEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      secrets: backendSecrets
      registries: [
        {
          server: registry.properties.loginServer
          username: acrCredentials.username
          passwordSecretRef: 'acr-password'
        }
      ]
      ingress: {
        external: true
        targetPort: 8000
        transport: 'auto'
        allowInsecure: false
      }
    }
    template: {
      containers: [
        {
          name: 'api'
          image: apiImage
          env: commonBackendEnv
          resources: {
            cpu: 0.5
            memory: '1Gi'
          }
          volumeMounts: [
            {
              volumeName: 'uploads'
              mountPath: '/app/uploads'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: apiMaxReplicas
      }
      volumes: [
        {
          name: 'uploads'
          storageType: 'AzureFile'
          storageName: uploadsMount.name
        }
      ]
    }
  }
  dependsOn: [
    uploadsMount
    postgresDatabase
    postgresAllowAzure
    postgresVectorExtension
  ]
}

resource workerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: workerAppName
  location: location
  properties: {
    managedEnvironmentId: acaEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      secrets: backendSecrets
      registries: [
        {
          server: registry.properties.loginServer
          username: acrCredentials.username
          passwordSecretRef: 'acr-password'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'worker'
          image: apiImage
          command: [
            'celery'
            '-A'
            'backend.celery_app'
            'worker'
            '--loglevel=info'
            '-Q'
            'default,file_processing'
          ]
          env: commonBackendEnv
          resources: {
            cpu: 0.5
            memory: '1Gi'
          }
          volumeMounts: [
            {
              volumeName: 'uploads'
              mountPath: '/app/uploads'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: workerMaxReplicas
      }
      volumes: [
        {
          name: 'uploads'
          storageType: 'AzureFile'
          storageName: uploadsMount.name
        }
      ]
    }
  }
  dependsOn: [
    uploadsMount
    postgresDatabase
    postgresAllowAzure
    postgresVectorExtension
  ]
}

resource schedulerApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: schedulerAppName
  location: location
  properties: {
    managedEnvironmentId: acaEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      secrets: backendSecrets
      registries: [
        {
          server: registry.properties.loginServer
          username: acrCredentials.username
          passwordSecretRef: 'acr-password'
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'scheduler'
          image: apiImage
          command: [
            'celery'
            '-A'
            'backend.celery_app'
            'beat'
            '--loglevel=info'
            '--schedule=/app/uploads/celerybeat-schedule'
          ]
          env: commonBackendEnv
          resources: {
            cpu: 0.25
            memory: '0.5Gi'
          }
          volumeMounts: [
            {
              volumeName: 'uploads'
              mountPath: '/app/uploads'
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 1
      }
      volumes: [
        {
          name: 'uploads'
          storageType: 'AzureFile'
          storageName: uploadsMount.name
        }
      ]
    }
  }
  dependsOn: [
    uploadsMount
    postgresDatabase
    postgresAllowAzure
    postgresVectorExtension
  ]
}

resource webApp 'Microsoft.App/containerApps@2024-03-01' = {
  name: webAppName
  location: location
  properties: {
    managedEnvironmentId: acaEnvironment.id
    configuration: {
      activeRevisionsMode: 'Single'
      secrets: [
        {
          name: 'acr-password'
          value: acrCredentials.passwords[0].value
        }
      ]
      registries: [
        {
          server: registry.properties.loginServer
          username: acrCredentials.username
          passwordSecretRef: 'acr-password'
        }
      ]
      ingress: {
        external: true
        targetPort: 3001
        transport: 'auto'
        allowInsecure: false
      }
    }
    template: {
      containers: [
        {
          name: 'web'
          image: webImage
          env: [
            {
              name: 'NEXT_PUBLIC_API_BASE_URL'
              value: publicWebhookBaseUrl
            }
          ]
          resources: {
            cpu: 0.5
            memory: '1Gi'
          }
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 3
      }
    }
  }
}

output acrLoginServer string = registry.properties.loginServer
output containerAppEnvironmentName string = acaEnvironment.name
output apiAppName string = apiApp.name
output webAppName string = webApp.name
output workerAppName string = workerApp.name
output schedulerAppName string = schedulerApp.name
output apiDefaultFqdn string = apiApp.properties.configuration.ingress.fqdn
output webDefaultFqdn string = webApp.properties.configuration.ingress.fqdn
output apiCustomHostName string = apiHostName
output webCustomHostName string = webHostName
output publicWebhookBaseUrl string = publicWebhookBaseUrl
