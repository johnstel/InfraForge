# InfraForge — App-Hosting IaC

This directory contains the Bicep template that deploys the **InfraForge application itself**
onto Azure App Service (Linux Python) backed by Azure SQL Database.
It is the authoritative IaC for the demo deployment topology described in the deployment
readiness review.

---

## Directory layout

```
iac/
├── main.bicep                  ← Template entrypoint (App Service + SQL)
├── parameters/
│   └── demo.bicepparam         ← Parameter values for demo deployments
└── README.md                   ← This file
```

---

## Prerequisites

| Tool | Install |
|------|---------|
| Azure CLI ≥ 2.60 | `winget install Microsoft.AzureCLI` |
| Bicep CLI (bundled with az) | `az bicep install` |
| Azure subscription with Contributor role | — |

---

## Quick start

### 1 — Fill in parameters

Edit `iac/parameters/demo.bicepparam` and replace every `<REQUIRED …>` placeholder:

| Parameter | How to obtain |
|-----------|---------------|
| `entraClientId` / `entraTenantId` / `entraClientSecret` | Azure Portal → Entra ID → App Registrations → New registration |
| `githubToken` | [github.com/settings/tokens](https://github.com/settings/tokens) — `repo` scope |
| `githubOrg` | Your GitHub org or personal username |
| `sessionSecret` | `python -c "import secrets; print(secrets.token_hex(32))"` |
| `sqlAdminPassword` | Any strong password meeting [Azure SQL policy](https://learn.microsoft.com/en-us/sql/relational-databases/security/password-policy) |

### 2 — Log in and set subscription

```bash
az login
az account set --subscription "<subscription-id>"
```

### 3 — Create the resource group

```bash
az group create \
  --name rg-infraforge-dev-eus2 \
  --location eastus2
```

---

## Validate (ARM what-if)

Preview every resource change **before** deploying — equivalent to `terraform plan`:

```bash
az deployment group what-if \
  --resource-group rg-infraforge-dev-eus2 \
  --template-file iac/main.bicep \
  --parameters iac/parameters/demo.bicepparam
```

Run a schema/policy validation without touching live resources:

```bash
az deployment group validate \
  --resource-group rg-infraforge-dev-eus2 \
  --template-file iac/main.bicep \
  --parameters iac/parameters/demo.bicepparam
```

Both commands are safe to run repeatedly — they make no changes.

---

## Deploy

```bash
az deployment group create \
  --name infraforge-demo \
  --resource-group rg-infraforge-dev-eus2 \
  --template-file iac/main.bicep \
  --parameters iac/parameters/demo.bicepparam
```

The deployment outputs the App Service URL, SQL FQDN, and the managed-identity
principal ID for downstream RBAC grants:

```
Outputs:
  appServiceUrl  = https://infraforge-dev-app.azurewebsites.net
  appServiceName = infraforge-dev-app
  sqlServerFqdn  = infraforge-dev-sql.database.windows.net
  sqlDatabaseName = InfraForgeDB
  principalId    = <guid>
```

### Post-deploy: grant the App Service access to your subscription (required)

InfraForge uses its system-assigned managed identity to call the Azure ARM API.
Grant the `Contributor` role so it can deploy customer templates:

```bash
PRINCIPAL_ID=$(az deployment group show \
  --name infraforge-demo \
  --resource-group rg-infraforge-dev-eus2 \
  --query properties.outputs.principalId.value -o tsv)

az role assignment create \
  --role Contributor \
  --assignee-object-id "$PRINCIPAL_ID" \
  --assignee-principal-type ServicePrincipal \
  --scope /subscriptions/<subscription-id>
```

---

## Deploy application code

After the infrastructure is up, push the application via the built-in zip-deploy:

```bash
# From the repository root
zip -r app.zip . \
  --exclude ".git/*" ".venv/*" "output/*" "*.pyc" "__pycache__/*"

az webapp deploy \
  --resource-group rg-infraforge-dev-eus2 \
  --name infraforge-dev-app \
  --src-path app.zip \
  --type zip
```

The startup command is auto-detected from `web_start.py`; if it is not picked up
automatically set it in the portal or via CLI:

```bash
az webapp config set \
  --resource-group rg-infraforge-dev-eus2 \
  --name infraforge-dev-app \
  --startup-file "python web_start.py"
```

---

## Teardown

```bash
az group delete --name rg-infraforge-dev-eus2 --yes --no-wait
```

---

## Template parameters reference

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `subscriptionId` | No | current subscription | Azure subscription ID |
| `location` | No | resource group location | Azure region |
| `environment` | No | `dev` | `dev` / `staging` / `prod` |
| `entraClientId` | **Yes** | — | Entra ID app client ID |
| `entraTenantId` | **Yes** | — | Azure AD tenant ID |
| `entraClientSecret` | **Yes** | — | Entra ID client secret |
| `githubToken` | **Yes** | — | GitHub PAT (repo scope) |
| `githubOrg` | **Yes** | — | GitHub org / username |
| `sessionSecret` | **Yes** | — | Session cookie signing secret |
| `sqlAdminLogin` | No | `sqladmin` | SQL Server admin login |
| `sqlAdminPassword` | **Yes** | — | SQL Server admin password |
| `copilotModel` | No | `gpt-4.1` | Copilot model ID |
| `copilotLogLevel` | No | `warning` | SDK log verbosity |

---

## Resources created

| Resource type | Name pattern | Notes |
|---------------|-------------|-------|
| `Microsoft.Sql/servers` | `infraforge-<env>-sql` | TLS 1.2, Azure-services firewall rule |
| `Microsoft.Sql/servers/databases` | `InfraForgeDB` | Basic SKU (2 GB) |
| `Microsoft.Web/serverfarms` | `infraforge-<env>-asp` | Linux B1 |
| `Microsoft.Web/sites` | `infraforge-<env>-app` | Python 3.12, system-assigned identity, HTTPS-only |
