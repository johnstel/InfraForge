// ──────────────────────────────────────────────────────────────
// InfraForge — App-Hosting IaC
// Deploys InfraForge itself: App Service (Linux Python) + Azure SQL
// + app settings wiring for a minimal demo deployment topology.
// ──────────────────────────────────────────────────────────────

targetScope = 'resourceGroup'

// ── Identity & subscription inputs ─────────────────────────

@description('Azure subscription ID where InfraForge will deploy resources.')
param subscriptionId string = subscription().subscriptionId

@description('Azure region for all resources.')
param location string = resourceGroup().location

@description('Short environment label (dev | staging | prod).')
@allowed(['dev', 'staging', 'prod'])
param environment string = 'dev'

// ── App settings: Entra ID ──────────────────────────────────

@description('Entra ID (Azure AD) application (client) ID.')
param entraClientId string

@description('Entra ID tenant ID.')
param entraTenantId string

@secure()
@description('Entra ID client secret.')
param entraClientSecret string

// ── App settings: GitHub ────────────────────────────────────

@secure()
@description('GitHub personal access token with repo scope.')
param githubToken string

@description('GitHub organization or personal account name.')
param githubOrg string

// ── App settings: Session ───────────────────────────────────

@secure()
@description('Random secret used to sign session cookies (32+ chars).')
param sessionSecret string

// ── App settings: Copilot ───────────────────────────────────

@description('Copilot model identifier.')
param copilotModel string = 'gpt-4.1'

@description('Copilot SDK log level.')
@allowed(['debug', 'info', 'warning', 'error'])
param copilotLogLevel string = 'warning'

// ── SQL admin credentials ───────────────────────────────────

@description('SQL Server administrator login name.')
param sqlAdminLogin string = 'sqladmin'

@secure()
@description('SQL Server administrator password.')
param sqlAdminPassword string

// ── Naming & Tags ───────────────────────────────────────────

var appName = 'infraforge'
var resourcePrefix = '${appName}-${environment}'
var tags = {
  application: 'InfraForge'
  environment: environment
  managedBy: 'InfraForge-IaC'
}

// ── SQL Server ──────────────────────────────────────────────

resource sqlServer 'Microsoft.Sql/servers@2023-08-01-preview' = {
  name: '${resourcePrefix}-sql'
  location: location
  tags: tags
  properties: {
    administratorLogin: sqlAdminLogin
    administratorLoginPassword: sqlAdminPassword
    minimalTlsVersion: '1.2'
    publicNetworkAccess: 'Enabled'
  }
}

resource sqlDb 'Microsoft.Sql/servers/databases@2023-08-01-preview' = {
  parent: sqlServer
  name: 'InfraForgeDB'
  location: location
  tags: tags
  sku: {
    name: 'Basic'
    tier: 'Basic'
  }
  properties: {
    collation: 'SQL_Latin1_General_CP1_CI_AS'
    maxSizeBytes: 2147483648 // 2 GB
    zoneRedundant: false
  }
}

// Allow Azure-internal traffic so the App Service can reach SQL
resource sqlFirewallAzure 'Microsoft.Sql/servers/firewallRules@2023-08-01-preview' = {
  parent: sqlServer
  name: 'AllowAzureServices'
  properties: {
    startIpAddress: '0.0.0.0'
    endIpAddress: '0.0.0.0'
  }
}

// ── App Service Plan (Linux, B1 — sufficient for demo) ──────

resource appServicePlan 'Microsoft.Web/serverfarms@2023-12-01' = {
  name: '${resourcePrefix}-asp'
  location: location
  tags: tags
  sku: {
    name: 'B1'
    tier: 'Basic'
  }
  properties: {
    reserved: true // Linux
  }
}

// ── Connection string helper ─────────────────────────────────
// ODBC connection string used by InfraForge at runtime.
// sqlAdminPassword is a @secure() parameter so this variable is
// treated as secure by Bicep and stored encrypted in ARM state.

var sqlConnectionString = 'Driver={ODBC Driver 18 for SQL Server};Server=tcp:${sqlServer.properties.fullyQualifiedDomainName},1433;Database=${sqlDb.name};Uid=${sqlAdminLogin};${sqlAdminPassword};Encrypt=yes;TrustServerCertificate=no;Connection Timeout=30'

// ── App Service (Python 3.12 on Linux) ──────────────────────

resource webApp 'Microsoft.Web/sites@2023-12-01' = {
  name: '${resourcePrefix}-app'
  location: location
  tags: tags
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlan.id
    httpsOnly: true
    siteConfig: {
      linuxFxVersion: 'PYTHON|3.12'
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      alwaysOn: false // B1 does not support AlwaysOn
      healthCheckPath: '/health'
      appSettings: [
        // ── Entra ID ────────────────────────────────────────
        { name: 'ENTRA_CLIENT_ID';     value: entraClientId }
        { name: 'ENTRA_TENANT_ID';     value: entraTenantId }
        { name: 'ENTRA_CLIENT_SECRET'; value: entraClientSecret }
        {
          name: 'ENTRA_REDIRECT_URI'
          value: 'https://${resourcePrefix}-app.azurewebsites.net/api/auth/callback'
        }
        // ── Azure SQL ────────────────────────────────────────
        { name: 'AZURE_SQL_CONNECTION_STRING'; value: sqlConnectionString }
        { name: 'AZURE_SQL_SERVER';            value: sqlServer.name }
        { name: 'AZURE_RESOURCE_GROUP';        value: resourceGroup().name }
        { name: 'AZURE_SUBSCRIPTION_ID';       value: subscriptionId }
        // ── GitHub integration ───────────────────────────────
        { name: 'GITHUB_TOKEN'; value: githubToken }
        { name: 'GITHUB_ORG';   value: githubOrg }
        // ── Copilot SDK ──────────────────────────────────────
        { name: 'COPILOT_MODEL';     value: copilotModel }
        { name: 'COPILOT_LOG_LEVEL'; value: copilotLogLevel }
        // ── Web server ───────────────────────────────────────
        { name: 'INFRAFORGE_WEB_HOST';       value: '0.0.0.0' }
        { name: 'INFRAFORGE_WEB_PORT';       value: '8080' }
        { name: 'INFRAFORGE_SESSION_SECRET'; value: sessionSecret }
        { name: 'INFRAFORGE_OUTPUT_DIR';     value: '/tmp/output' }
        // ── Python startup ───────────────────────────────────
        { name: 'SCM_DO_BUILD_DURING_DEPLOYMENT'; value: 'true' }
        { name: 'WEBSITE_RUN_FROM_PACKAGE';       value: '0' }
      ]
    }
  }
}

// ── Outputs ──────────────────────────────────────────────────

output appServiceUrl string = 'https://${webApp.properties.defaultHostName}'
output appServiceName string = webApp.name
output sqlServerFqdn string = sqlServer.properties.fullyQualifiedDomainName
output sqlDatabaseName string = sqlDb.name
output principalId string = webApp.identity.principalId
