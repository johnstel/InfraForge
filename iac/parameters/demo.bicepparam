// ──────────────────────────────────────────────────────────────
// InfraForge demo deployment parameters
// Fill in every value marked <REQUIRED> before deploying.
// See iac/README.md for full deployment instructions.
// ──────────────────────────────────────────────────────────────

using '../main.bicep'

// ── Subscription / region ────────────────────────────────────
param location        = 'eastus2'
param environment     = 'dev'

// ── Entra ID — create an App Registration first ─────────────
// Azure Portal → Entra ID → App Registrations → New registration
param entraClientId     = '<REQUIRED: Entra app client ID>'
param entraTenantId     = '<REQUIRED: Azure AD tenant ID>'
param entraClientSecret = '<REQUIRED: Entra client secret>'

// ── GitHub — PAT with repo scope ────────────────────────────
param githubToken = '<REQUIRED: GitHub PAT>'
param githubOrg   = '<REQUIRED: GitHub org or username>'

// ── Session secret — generate with:
//    python -c "import secrets; print(secrets.token_hex(32))"
param sessionSecret = '<REQUIRED: 32-char random secret>'

// ── SQL credentials ──────────────────────────────────────────
param sqlAdminLogin    = 'sqladmin'
param sqlAdminPassword = '<REQUIRED: SQL admin password>'

// ── Copilot (optional overrides) ─────────────────────────────
param copilotModel    = 'gpt-4.1'
param copilotLogLevel = 'warning'
