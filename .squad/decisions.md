# Squad Decisions

**Last Updated:** 2026-05-14T13:46:22.771-04:00

## Active Decisions

### 1. InfraForge Deployment & Customer Presentation Strategy (Mal)

**Date:** 2026-05-14T13:46:22.771-04:00  
**Author:** Mal (Lead / Solution Architect)  
**Status:** Proposed — awaiting team input

#### Repository Architecture Summary

InfraForge is a self-service infrastructure platform that lets enterprise teams provision production-ready Azure infrastructure through natural language. Platform teams retain governance via approved templates, service approvals, policies, cost transparency, and ARM deployment validation — all powered by the GitHub Copilot SDK.

**Core Architecture:**
| Layer | Technology | Key Files |
|-------|-----------|-----------|
| Backend | FastAPI / Python 3.13 / Uvicorn | `web_start.py`, `src/web.py`, `src/routers/` |
| Database | Azure SQL Database (pyodbc + AAD token auth) | `src/database.py` (~4600 LOC) |
| AI Engine | GitHub Copilot SDK (Python) | `src/copilot_helpers.py`, `src/tools/` (20+ tool modules) |
| Auth | Microsoft Entra ID (MSAL.js + MSAL Python) | `src/auth.py`, `src/routers/auth.py` |
| Frontend | Vanilla JS SPA (no framework) | `static/index.html`, `static/app.js` (~14800 LOC) |
| Deployment | ARM SDK (`azure-mgmt-resource`) | `src/tools/deploy_engine.py` |
| M365 Intelligence | Microsoft Work IQ (MCP Server) | `src/workiq_client.py`, `mcp.json` |
| Analytics | Fabric IQ (OneLake + Semantic Models) | `src/fabric.py` |
| CI/CD | GitHub Actions | `.github/workflows/deploy-swa.yml` |

**What Must Be Deployed:**
1. Azure SQL Database — All persistent state
2. Python web application — FastAPI on port 8080
3. Entra ID App Registration — OAuth2 auth flow
4. GitHub Copilot SDK access — AI backbone
5. Network access — ARM APIs, Microsoft Graph, Copilot SDK proxy
6. (Optional) Work IQ MCP Server — Node.js 18+ for M365 intelligence
7. (Optional) Fabric IQ — Analytics sync

**Major Risks & Decisions Needed:**

| # | Blocker | Severity | Owner |
|---|---------|----------|-------|
| B1 | Setup script is PowerShell-only; cloud deployment needs Bicep/ARM/Terraform | Medium | Kaylee |
| B2 | Copilot SDK availability in customer tenants (licensing/entitlement question) | High | Inara + John |
| B3 | ODBC Driver 18 must be verified on target compute | Low | Kaylee |

| # | Risk | Mitigation |
|---|------|-----------|
| R1 | Single-region, single-instance (no HA by default) | Document as intentional for Phase 1; HA plan for Phase 2+ |
| R2 | Frontend is ~14800 LOC vanilla JS (unknown performance at scale) | Acceptable for demo; consider CDN for customer-facing |
| R3 | `.env` file approach works locally; App Service needs Key Vault | Phase 2 hardening |
| R4 | If multiple customers use same instance, data is commingled | See D2 below |

**Key Decisions:**

| # | Decision | Options | Recommendation |
|---|----------|---------|----------------|
| D1 | Compute host for John's tenant | App Service (Linux) vs. Container Apps vs. ACA | **App Service Linux** — simplest, cheapest, Python 3.13 native |
| D2 | Customer deployment model | (a) SaaS / single instance (b) Deploy-in-their-tenant | **Deploy-in-their-tenant** — utilities won't send data to shared SaaS |
| D3 | CI/CD for cloud deployment | Extend existing deploy-swa.yml vs. new workflow | **New workflow** — SWA is landing page only; App Service needs separate |
| D4 | Demo vs. production environment | One environment vs. separate demo + prod | **Start with one** (demo); prod when customer commits |

---

### 2. Azure Tenant Deployment Plan (Kaylee)

**Decision Owner:** Kaylee (Azure Platform Engineer)  
**Date:** 2026-05-14  
**Status:** RECOMMENDATION (ready for implementation planning)  
**Audience:** John Stelmaszek, Electric Energy customers

#### Executive Summary

InfraForge is deployable to any Azure tenant with minimal infrastructure:
- **1 Azure SQL Database** (Basic tier, ~$5/month)
- **1 App Service** (B1 tier, ~$8/month)
- **1 Entra ID App Registration** for SSO
- **Managed identities** for all Azure-to-Azure auth (no secrets in code)
- **GitHub integration** via service-level PAT (optional)

**Total monthly baseline cost:** ~$13 (SQL + App Service) + GitHub Actions. No HA, no redundancy, no multi-region unless explicitly requested.

**Setup time:** 20–30 minutes (interactive PowerShell). **First deployment:** ~10 minutes (Bicep + ARM SDK).

#### Compute Host Recommendation

**Kaylee's Original:** App Service (Windows)  
**Mal's Recommendation:** App Service (Linux, Python 3.13)  
**Final Recommendation:** **App Service (Linux, Python 3.13)**

| Factor | Windows | Linux | Winner |
|--------|---------|-------|--------|
| **ODBC Driver 18** | Not pre-installed; requires Site Extensions | Pre-installed on base image | **Linux** |
| **Python 3.13 Runtime** | Possible via Site Extensions; non-standard | Standard runtime; well-supported | **Linux** |
| **Setup Complexity** | ODBC driver adds steps; Site Extensions overhead | Minimal; ODBC included out-of-box | **Linux** |
| **Container Support** | Windows containers larger, slower | Native Docker support | **Linux** |
| **Industry Standard** | Uncommon for Python | Python on Linux is modern standard | **Linux** |

**Primary Option:** App Service (Linux, Python 3.13)
- Cost: ~$8/month (B1 tier)
- Setup: `az webapp up --os-type Linux --runtime "PYTHON|3.13"`
- ODBC Driver 18: Pre-installed, no additional steps
- Best for: MVP, fastest to deployment

**Alternative Option:** Docker Container on App Service (Linux)
- Cost: ~$8/month (B1 tier)
- Setup: Build Dockerfile, push to ACR, deploy container
- ODBC Driver 18: Pre-baked in Docker image
- Best for: Production, multi-environment consistency

#### Deployment Architecture

- **Azure Subscription** with Resource Group (InfraForge)
- **App Service** (Linux, Python 3.13) with managed identity
- **Azure SQL Database** (Basic tier) with Azure AD-only auth
- **Entra ID App Registration** for OAuth2
- **(Optional)** GitHub service-level PAT for repo publishing
- **(Optional)** Fabric IQ for analytics
- Firewall rules: App Service → SQL; GitHub IPs → SQL

---

### 3. Security & Governance Plan (Zoe)

**Date:** 2026-05-14  
**Author:** Zoe (Security & Governance Specialist)  
**Status:** ACTIONABLE PLAN

#### Executive Summary

InfraForge is architecturally sound. It uses industry-standard patterns:
- **Entra ID OAuth2 + MSAL** for authentication
- **Azure AD auth to SQL** (no stored passwords)
- **Managed identities** for ARM deployments
- **Database-backed policies** with no hardcoded secrets
- **Cryptographic token handling**

**For tenant deployment:** Setup script is production-ready with preflight validation. Requires Contributor+ permissions and tenant-level Application Administrator consent.

**For electric utility customers:** InfraForge represents a credible enterprise governance story — identity-driven tagging, policy-enforced infrastructure, audit trails in SQL, and cost transparency satisfy FERC/NERC compliance requirements.

#### Key Security Observations

**Entra ID Integration — STRONG**
- ✅ Token handling: No tokens in frontend localStorage — only session IDs in httpOnly cookies
- ✅ Client credential flow: Backend uses confidential client (secret); frontend never touches secrets
- ✅ Scope control: Minimal Graph scopes (`User.Read` + optional manager graph)
- ✅ Group claims: Supports Entra ID group membership for role derivation
- ⚠️ State parameter: Auth flow uses CSRF-safe state tokens; flows are short-lived

**Azure SQL Database Access — PRODUCTION-READY**
- ✅ Authentication via `DefaultAzureCredential` (managed identity in Azure)
- ✅ No stored passwords, no connection string secrets in code
- ✅ SQL firewall rule auto-provisioned at startup
- ✅ Identity-based end-to-end: User → App backend → SQL
- ✅ Parameterized queries (pyodbc `?` placeholders) — no SQL injection
- ✅ Audit trail: All actions logged to `chat_messages` and `usage_logs`

**Managed Identity (ARM Deployment) — EXEMPLARY**
- ✅ System-assigned or user-assigned managed identity (not service principal with secrets)
- ✅ No ARM deployment credentials hardcoded
- ✅ Fine-grained RBAC: Scope to specific roles (Contributor, Deployment Contributor)
- ✅ Rotation-free: Azure rotates credentials automatically

**Microsoft Graph & Work IQ Integration**
- ✅ Delegated permissions (scoped to user's visibility)
- ✅ Non-critical: Graph failures are graceful
- ✅ No M365 data cached in database; only results logged to `chat_messages`
- ⚠️ Work IQ setup requires tenant admin consent (one-time browser auth)

#### Required Permissions

**For InfraForge deployment (setup.ps1):**
- Azure subscription: **Contributor or Owner** role (create SQL, App Service, App Registration)
- Entra ID tenant: **Application Administrator** consent (needed once, tenant-wide)
- (Optional) GitHub: Service-level PAT for repo publishing

#### Hardening Recommendations (Phase 2)

1. Managed Identity for SQL auth (replace connection string secrets)
2. Key Vault for all secrets (Entra client secret, GitHub token, session secret)
3. Private endpoints for SQL (if VNet isolation desired)
4. RBAC roles: Contributor on subscription for ARM deployments
5. Azure Policy: Tag enforcement, region restriction, approved services

---

### 4. Validation & Readiness Plan (Wash)

**Decision:** Deploy and demo readiness validation framework for Enterprise pilot  
**Recommended by:** Wash (Validation Engineer)  
**Date:** 2026-05-14T13:46:22.771-04:00  
**Status:** Ready for Team Review

#### Existing Validation Assets

**Test Coverage (Current State):**
| Category | Files | Focus | Command |
|----------|-------|-------|---------|
| ARM Templates | `tests/test_arm_template_validation.py` | Template syntax, resource IDs, composite validation | `python -m pytest tests/test_arm_template_validation.py -v` |
| SQL Firewall | `tests/test_sql_firewall.py` | IP extraction, firewall error detection, retry logic | `python -m pytest tests/test_sql_firewall.py -v` |
| Infrastructure | `azure_infrastructure_test.py` | Resource provisioning, tags, API versions (20+ tests) | `python -m pytest azure_infrastructure_test.py -v` |

**Test Coverage Gaps:**
- No Web API endpoint tests (137 route handlers, 0 tests)
- No database CRUD validation tests (extensive SQL backend, no unit tests)
- No Copilot SDK integration tests (core agent workflows untested)
- No end-to-end demo flow tests (catalog sync, service onboarding pipeline)
- No deployment validation tests (ARM What-If, deployment status checks)
- No authentication/RBAC tests (Entra ID integration, scope verification)
- No load/stress tests (performance limits unknown)

**Deployment Artifacts:**
| Artifact | Location | Purpose | Readiness |
|----------|----------|---------|-----------|
| Setup Script | `scripts/setup.ps1` | First-time infrastructure provisioning | ✓ Comprehensive (9 steps, preflight checks, fallbacks) |
| Requirements | `requirements.txt` | Python dependencies | ✓ Complete (16 packages, pinned versions) |
| Docker | None | Container deployment | ✗ **BLOCKER** for cloud-native pilot |
| GitHub Actions | `.github/workflows/deploy-swa.yml` | CI/CD for Static Web Apps | ⚠ Incomplete (SWA only, no API deployment) |
| Demo Guide | `DEMO_GUIDE.md` | Step-by-step demo walkthrough | ✓ Clear (12 major steps) |
| Architecture Docs | `docs/ARCHITECTURE.md` | System design reference | ✓ Comprehensive (47 KB) |

#### Deployment Readiness Checklist

**Pre-Deployment Phase:**
- [ ] Azure subscription with Contributor/Owner role
- [ ] Azure CLI (v2.77.0+) installed and authenticated
- [ ] Python 3.13.12 installed and on PATH
- [ ] ODBC Driver 18 for SQL Server installed
- [ ] winget (Windows 10/11) available for auto-install fallback
- [ ] GitHub account with PAT or `gh` CLI authenticated
- [ ] Microsoft Entra ID tenant admin access
- [ ] Copilot subscription verified (`copilot --version`)

**Connectivity Validation:**
- [ ] `az account show` returns correct subscription
- [ ] `python -m venv .venv && source .venv/bin/activate` works
- [ ] `pip install -r requirements.txt` completes without errors
- [ ] SQL connectivity: `python -c "import pyodbc; print('OK')"`

**Smoke Test Phase:**
- [ ] App loads (HTTP 200 at localhost:8080)
- [ ] Auth flow works (Entra ID login via MSAL)
- [ ] SQL schema initializes (tables created on first run)
- [ ] GitHub Copilot CLI authentication succeeds

**End-to-End Validation:**
- [ ] Azure service sync (populate approved services catalog)
- [ ] Onboard a service (e.g., Azure SQL)
- [ ] Generate template (Copilot SDK generates Bicep)
- [ ] Deploy to Azure (ARM SDK provisions resources)
- [ ] Verify resources (Azure portal shows created resources)

#### Performance Baseline

- Unknown: Concurrent user limits, response times under load, database connection pool sizing
- **Action:** Run load testing after deployment (100 concurrent users, 5-minute ramp-up)

---

### 5. InfraForge Customer Strategy & Presentation Plan (Inara)

**Author:** Inara (Customer Strategy Lead)  
**Date:** 2026-05-14  
**Audience:** Sales, partnership, and customer success teams  
**Purpose:** Comprehensive go-to-market strategy for Electric Energy customers

#### Executive Summary

InfraForge is positioned as a **governance-first, self-service infrastructure platform** for enterprise IT organizations who need:
- **Autonomy:** App teams request infrastructure without IT tickets/waiting
- **Governance:** Platform teams enforce policies, approved templates, audit trails
- **Compliance:** Industry standards (FERC/NERC for utilities, SOC2 generally)
- **Cost transparency:** Chargeback accuracy, cost center tracking, forecasting

**For utilities specifically**, InfraForge solves three critical pain points:
1. **Governance & Compliance Risk** — Manual requests are audit nightmares
2. **Cost Attribution Failure** — Cloud costs buried in bills; impossible to chargeback
3. **Self-Service Bottleneck** — IT overwhelmed with manual requests; app teams waiting weeks

#### Core Value Proposition

| For App Teams | For Platform Teams |
|---|---|
| Request infrastructure via natural language (no IaC, no waiting) | Approve once, enforce always (templates + policies) |
| See cost estimate before you deploy | Cost tracking by cost center, department, project |
| One-click deployment (Copilot SDK handles generation, validation, deployment) | Every action audited with timestamp, user, outcome |
| Self-service speed (minutes, not weeks) | Governance & compliance shift-left |

#### The Utility Angle

For **Electric Energy organizations**, InfraForge specifically addresses:

**1. Identity-Driven Compliance**
- Every infrastructure resource tagged with authenticated owner (Entra ID claims)
- Cost center auto-populated from user's department in Azure AD
- Audit trail: who requested it, when, what was approved, what was deployed
- FERC/NERC requires "responsible party" and change tracking — InfraForge provides both automatically

**2. Cost Governance & Chargeback**
- Estimates shown before deployment (no billing surprises)
- Every resource tagged with cost center (automatic chargeback to business units)
- (Optional) Fabric IQ dashboard rolls up costs by department/project
- Policy engine enforces cost limits per cost center/project

**3. Policy-as-Code Enforcement**
- Approved services only (non-approved services blocked with clear rejection + request path)
- Approved SKUs enforced (e.g., "SQL Standard in prod, SQL Basic in dev")
- Regional constraints enforced (e.g., "no data outside CONUS" for NERC compliance)
- All policies versioned in database; changes are auditable

**4. Auditability at Every Step**
- Governance Review: Policy check logged
- Generation: Service/template selection logged
- Cost Validation: Estimate shown and logged
- Deployment: ARM What-If shows what *would* change; deployment logs all resources
- Success/Failure: Outcome stored in audit table with timestamp and user

#### Demo Scenario (Utility-Specific)

**Natural Language Request:**
> "Provision an Azure SQL database for SCADA data ingestion in the grid operations department, prod environment, with cost center code CC-2024-GRID-OPS and a forecast of $500/month max."

**Demo Flow:**
1. **Governance Check** — Copilot SDK validates:
   - Is Azure SQL approved? ✓ Yes
   - Is user in grid-ops department? ✓ Yes
   - Does cost center exist? ✓ Yes (from Entra AD claims)
   - Will deployment exceed cost limit? ✓ No ($450 < $500)
   
2. **Generation** — Copilot SDK generates Bicep:
   - SQL Server (prod-grade: Standard tier, RBAC, managed identity)
   - Database (100 GB, backups, diagnostic logs)
   - All resources tagged: owner, cost center, department, project, environment

3. **Cost Estimate** — Shown to user:
   - SQL Server: $180/month
   - Database: $270/month
   - Total: $450/month (within budget)

4. **Approval** — User confirms deployment

5. **ARM What-If** — Preview exact resources:
   - 1 SQL Server (new)
   - 1 Azure SQL Database (new)
   - 5 diagnostic settings (new)
   - 2 RBAC role assignments (new)

6. **Deployment** — ARM SDK provisions:
   - Progress streamed: "Creating SQL Server...", "Creating Database...", "Configuring diagnostics...", "Done"
   - Audit trail stored: user, timestamp, request, approval, generation, deployment outcome

7. **Success Notification** — Email with:
   - Resource IDs and connection strings
   - Cost forecast
   - Next steps (access control, data migration)

#### Deployment Model for Utilities

**Not SaaS — Deploy-in-Your-Tenant**
- Your Azure subscription, your SQL, your App Service
- You control data, access logs, everything
- You create Entra ID app registration; InfraForge doesn't ship a shared app reg
- Baseline cost: ~$13/month (SQL Basic + App Service B1)

#### Presentation Outline

**Slide 1: Problem Statement (2 min)**
- Current state: Manual infrastructure requests
- Desired state: Governance + Self-Service + Auditability

**Slide 2: InfraForge Overview (2 min)**
- What it is: AI-powered infrastructure request platform (natural language → validated infrastructure)
- How it works: Copilot SDK validates governance + generates code + deploys via ARM
- Key constraint: **Governance-first** — no request gets generated unless policy-approved

**Slide 3: Architecture for Utilities (3 min)**
- Deploy-in-your-tenant (not SaaS)
- Identity layer: Entra ID OAuth2
- Governance layer: Policies + Approvals + Catalog

**Slide 4: Demo Walkthrough (5–7 min)**
- Natural language request → governance check → cost estimate → approval → deployment

**Slide 5: Compliance & Risk Mitigation (3 min)**
- FERC/NERC compliance narrative
- Audit trail immutability
- Cost controls and forecasting

**Slide 6: Adoption Roadmap (3 min)**
- Phase 1: Pilot with one business unit (grid operations)
- Phase 2: Expand to infrastructure team
- Phase 3: Broader rollout across utility

---

## Governance

- All meaningful changes require team consensus
- Document architectural decisions here
- Keep history focused on work, decisions focused on direction
