using './main.bicep'

param namePrefix = 'ragmind'
param location = 'westeurope'
param rootDomain = 'example.com'

// The deploy script fills these after pushing images to ACR.
param apiImage = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'
param webImage = 'mcr.microsoft.com/azuredocs/containerapps-helloworld:latest'

param postgresAdminLogin = 'ragmindadmin'
param postgresAdminPassword = readEnvironmentVariable('AZURE_POSTGRES_ADMIN_PASSWORD', '')
param authJwtSecretKey = readEnvironmentVariable('AUTH_JWT_SECRET_KEY', '')
param authAdminPassword = readEnvironmentVariable('AUTH_ADMIN_PASSWORD', '')
param botTokenEncryptionKey = readEnvironmentVariable('BOT_TOKEN_ENCRYPTION_KEY', '')
param groqApiKey = readEnvironmentVariable('GROQ_API_KEY', '')
param cohereApiKey = readEnvironmentVariable('COHERE_API_KEY', '')
param platformOwnerUsername = readEnvironmentVariable('PLATFORM_OWNER_USERNAME', '')

param llmProvider = 'groq-llama-3.3-70b-versatile'
param embeddingProvider = 'cohere'
param answerMaxTokens = 1024
param apiMaxReplicas = 3
param workerMaxReplicas = 3
