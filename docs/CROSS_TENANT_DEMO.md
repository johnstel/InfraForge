# InfraForge — Cross-Tenant Demo Deployment Guide

This guide explains how to deploy InfraForge into a **customer's own Azure tenant**
for a managed demo handoff, instead of running it in the operator's subscription.

---

## When to Use This Guide

Use the cross-tenant deployment path when:

- You are handing off a live InfraForge demo to a **new customer** in their own
  Azure environment.
- The customer's Azure admin has asked you to provision InfraForge directly into
  their subscription.
- You are repeating a demo across multiple customer tenants and need a **repeatable,
  parameterized** setup that avoids manual rework each time.

For a standard single-tenant (operator's own subscription) deployment, follow the
regular [setup guide](SETUP.md) — you do **not** need this document.

---

## Parameter Contract

The table below defines every value that must be collected from the customer before
running the cross-tenant setup.

### Customer-provided inputs

| Parameter | Flag | Env Var | Format | Required? | Who provides |
|-----------|------|---------|--------|-----------|--------------|
| Customer tenant ID | `-CustomerTenantId` | `CUSTOMER_TENANT_ID` | GUID | Yes | Customer Azure admin |
| Customer subscription ID | `-CustomerSubscriptionId` | `CUSTOMER_SUBSCRIPTION_ID` | GUID | Yes | Customer Azure admin |
| Preferred region | `-CustomerRegion` | `CUSTOMER_REGION` | Azure region string (e.g. `eastus2`) | No (defaults to `eastus2`) | Customer Azure admin |
| App registration client ID | `-CustomerAppClientId` | `CUSTOMER_APP_CLIENT_ID` | GUID | No — setup creates one if omitted | Customer Azure admin |
| App registration client secret | `-CustomerAppClientSecret` | `CUSTOMER_APP_CLIENT_SECRET` | string | Required when client ID is provided | Customer Azure admin |

### Operator-owned inputs

These values come from the operator's own environment and are **not** customer-provided:

| Value | Source |
|-------|--------|
| Operator Azure login | `az login` (operator's own account) |
| SQL server name / DB | Auto-generated or via `-SqlServerName` / `-SqlDatabaseName` |
| Resource group | `-ResourceGroup` (default: `InfraForge`) |
| GitHub token / org | `gh` CLI or `GITHUB_TOKEN` env var |
| Copilot model | `.env` — `COPILOT_MODEL` |

---

## Prerequisites

All standard [prerequisites](SETUP.md#prerequisites) apply, plus:

1. **Operator must be a Guest or have Contributor access in the customer tenant.**
   The customer admin must either:
   - Invite the operator as a Guest user and grant Contributor on the target subscription, **or**
   - Run the setup themselves after being handed the commands below.
2. **Customer must have an Azure subscription** (Pay-As-You-Go, EA, MCA, or CSP).
3. **Customer must supply the values** listed in the table above (see
   [Collecting Customer Values](#collecting-customer-values)).

---

## Collecting Customer Values

Send the customer's Azure admin the following checklist.

> **Note for customers:** You do not need to install anything. Just gather the
> values below from the Azure Portal and share them with the operator.

```
Azure Tenant ID
  Location: Azure Portal → Azure Active Directory → Overview → Tenant ID
  Format:   xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

Azure Subscription ID
  Location: Azure Portal → Subscriptions → <subscription name> → Subscription ID
  Format:   xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx

Preferred Azure Region  (optional, default: eastus2)
  Examples: eastus2, westeurope, australiaeast

Pre-existing App Registration  (optional — operator can create one)
  If you already have an Entra ID app registration for InfraForge:
    Client ID:     Azure Portal → App Registrations → <app> → Application (client) ID
    Client Secret: Azure Portal → App Registrations → <app> → Certificates & Secrets
```

---

## Usage

### 1. Dry-run validation (recommended first step)

Validate the collected parameters without creating any Azure resources.
This is safe to run against the customer tenant at any time.

```powershell
.\scripts\setup.ps1 `
    -CustomerTenantId     "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" `
    -CustomerSubscriptionId "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy" `
    -CustomerRegion       "eastus2" `
    -DryRun
```

Expected output:

```
╔══════════════════════════════════════════════════════╗
║       InfraForge — Dry-Run Validation                ║
╚══════════════════════════════════════════════════════╝

  All parameters are valid. Setup plan (no resources will be created):

  Mode:                 Cross-tenant demo deployment
  Customer Tenant ID:   xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
  Customer Sub ID:      yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy
  Customer Region:      eastus2
  App Registration:     (will create in customer tenant)
  Resource Group:       InfraForge
  SQL Server:           infraforge-sql-<random>
  SQL Database:         InfraForgeDB

  Re-run without -DryRun to provision these resources.
```

### 2. Full cross-tenant setup

```powershell
.\scripts\setup.ps1 `
    -CustomerTenantId       "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" `
    -CustomerSubscriptionId "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy" `
    -CustomerRegion         "eastus2"
```

### 3. Cross-tenant setup with a pre-existing app registration

If the customer already has an Entra ID app registration:

```powershell
.\scripts\setup.ps1 `
    -CustomerTenantId       "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" `
    -CustomerSubscriptionId "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy" `
    -CustomerAppClientId    "appid-guid-goes-here" `
    -CustomerAppClientSecret "the-client-secret" `
    -SkipEntraId
```

### 4. Non-interactive cross-tenant setup (CI / scripted handoff)

```powershell
.\scripts\setup.ps1 `
    -CustomerTenantId       "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" `
    -CustomerSubscriptionId "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy" `
    -CustomerRegion         "eastus2" `
    -Yes
```

### 5. Using an env template file

Supply a `.env` template to seed customer-specific defaults before the operator's
generated values are merged in:

```powershell
.\scripts\setup.ps1 `
    -CustomerTenantId       "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx" `
    -CustomerSubscriptionId "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy" `
    -EnvTemplate            ".\customer-acme-corp.env.template" `
    -Yes
```

---

## What the Setup Script Does Differently in Cross-Tenant Mode

| Step | Single-tenant | Cross-tenant |
|------|--------------|--------------|
| Resource group | Created in operator subscription | Created in customer subscription |
| SQL Server | Operator subscription | Customer subscription |
| App registration | Operator tenant | Customer tenant (or reuse existing) |
| `.env` output | `AZURE_SUBSCRIPTION_ID` = operator sub | + `CUSTOMER_TENANT_ID`, `CUSTOMER_SUBSCRIPTION_ID`, `CUSTOMER_REGION` |
| Env template | Not used | Seeded from `-EnvTemplate` if provided |

The cross-tenant values are written to `.env` under the `CUSTOMER_*` keys.
InfraForge uses these at runtime to target the customer subscription for ARM
deployments while the operator's SQL / auth credentials remain intact.

---

## Required Permissions in the Customer Tenant

The account running setup (or the customer's admin) needs:

| Permission | Minimum Role | Step | Purpose |
|-----------|-------------|------|---------|
| Create resource groups | **Contributor** | Step 1 | `az group create` |
| Create SQL servers / databases | **Contributor** | Step 2 | `az sql server create` |
| Create app registrations | Application Developer *or* tenant setting enabled | Step 3 | `az ad app create` |
| Register resource providers | **Contributor** | Step 4 | `az provider register` |

See [Required Permissions](SETUP.md#required-permissions) for the full matrix.

---

## Known Failure Modes & Remediation

### "customer_subscription_id is required when customer_tenant_id is provided"

You supplied `-CustomerTenantId` without `-CustomerSubscriptionId`.

**Fix:** Always provide both flags together:
```powershell
-CustomerTenantId "..." -CustomerSubscriptionId "..."
```

---

### "customer_tenant_id '...' is not a valid GUID"

The value supplied for `-CustomerTenantId` is not a well-formed GUID.

**Fix:** Locate the correct value in the Azure Portal:
> Azure Active Directory → Overview → **Tenant ID**

The format is `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` (8-4-4-4-12 hex groups).

---

### "No Contributor or Owner role found on subscription"

The operator's (or customer admin's) account does not have sufficient RBAC on
the customer subscription.

**Fix options:**
- Ask the customer admin to assign Contributor:
  ```powershell
  az role assignment create --role Contributor `
      --assignee <operator-oid> `
      --scope /subscriptions/<customer-sub-id>
  ```
- Have the customer admin run setup themselves using the same commands.

---

### "Failed to create app registration" in customer tenant

The customer tenant restricts application registration to admins.

**Fix options:**
1. Customer admin enables *"Users can register applications"* in
   **Entra ID → User Settings**.
2. Customer admin creates the app registration manually and supplies the
   `client ID` and `client secret` via `-CustomerAppClientId` / `-CustomerAppClientSecret`.
3. Run with `-SkipEntraId` and configure authentication manually post-setup.

---

### "SQL Server creation failed" in customer subscription

Region quota exhausted, or the `Microsoft.Sql` resource provider is not registered
in the customer subscription.

**Fix:**
- Try a different region: `-CustomerRegion westus2`
- The setup script auto-tries fallback regions (`centralus`, `westus2`, `eastus`, …)
- If all regions fail, check quotas in **Azure Portal → Subscriptions → Usage + quotas**

---

### "customer_region '...' is not in the known-regions list"

This is a **warning**, not an error. The region name may be correct (e.g. a new
Azure region or a sovereign cloud endpoint) but is not in the built-in list.

**Fix:** Verify the region string at
[Azure regions](https://azure.microsoft.com/en-us/explore/global-infrastructure/geographies/).
If valid, you can proceed — the warning is informational only.

---

### Cross-tenant `.env` values not taking effect

After setup, InfraForge still targets the operator subscription.

**Fix:** Confirm `CUSTOMER_TENANT_ID` and `CUSTOMER_SUBSCRIPTION_ID` are present
in `.env`:
```powershell
Select-String -Path .env -Pattern "^CUSTOMER_"
```

If missing, re-run setup with the `-Force` flag to regenerate the `.env` file.

---

## Operator vs Customer Responsibilities — Summary

| Task | Operator | Customer |
|------|----------|----------|
| Run `scripts/setup.ps1` | ✅ | Optional |
| Provide tenant ID | | ✅ |
| Provide subscription ID | | ✅ |
| Grant operator Contributor access | | ✅ |
| Grant app registration permission (if restricted) | | ✅ |
| Provide pre-existing app registration (optional) | | ✅ |
| Set preferred region | | ✅ (optional) |
| Maintain operator SQL / GitHub credentials | ✅ | |
| Dry-run validation before setup | ✅ | |

---

## Related Docs

- [Setup Guide](SETUP.md) — single-tenant / operator setup
- [Architecture Reference](ARCHITECTURE.md) — system design
- [`.env.example`](../.env.example) — annotated env template with all variables
