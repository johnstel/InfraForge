# Zoe History

## Seed Context

- **Project:** InfraForge
- **Requested by:** John Stelmaszek
- **Description:** Self-service infrastructure platform for enterprise teams to provision production-ready Azure infrastructure from natural language while platform teams retain governance through approved templates, service approvals, policies, cost transparency, and deployment validation.
- **Stack:** FastAPI/Python 3.13 backend, Azure SQL Database, GitHub Copilot SDK, Microsoft Entra ID, Microsoft Graph, Microsoft Work IQ MCP, Fabric IQ, vanilla JavaScript SPA, ARM SDK deployment engine.

## Learnings

### 2026-05-14 — Security & Governance Assessment for Tenant Deployment & Customer Presentation

**Scope:** Full security architecture review of InfraForge; planning for customer deployment to Consumers Energy and similar electric utilities.

**Key findings:**

1. **Identity architecture is production-grade:**
   - MSAL.js (frontend) + MSAL Python (backend) with proper token lifecycle (no localStorage secrets, httpOnly cookies for session IDs)
   - Entra ID integration extracts rich organizational context (email, department, cost center, manager, groups)
   - Microsoft Graph enrichment is graceful (non-fatal failures)
   - Group claims enable role-based access control (PlatformTeam vs. standard users)

2. **SQL access is identity-based end-to-end:**
   - Azure SQL with AD-only authentication (no username/password)
   - DefaultAzureCredential picks up managed identity (Azure) or Azure CLI (local dev)
   - Parameterized queries (pyodbc with `?` placeholders) eliminate SQL injection
   - Firewall rule auto-managed at startup with IP detection + retry logic
   - Audit trail in database: all user actions timestamped, immutable, queryable

3. **ARM deployment uses managed identities, not secrets:**
   - Generated Bicep defaults to managed identity for resource authentication
   - No service principal secrets in CI/CD pipelines or generated code
   - Credential rotation is automatic (Azure-managed)

4. **Governance is database-driven, not hardcoded:**
   - All policies live in `governance_policies` table (versioned, auditable)
   - Security standards in `security_standards` table with validation keys + remediation
   - Compliance frameworks linked to controls (CIS, HIPAA, SOC2 etc.)
   - CISO/CTO review gates enforce structured verdicts before deployment

5. **Three-layer approval system:**
   - Service approval (catalog membership)
   - Policy compliance (governance validation)
   - CISO/CTO review (optional, structured)
   - All gates are audit-logged with timestamps and evidence

6. **Risks identified (all mitigable):**
   - Graph API scopes need Entra ID admin consent (post-setup checklist)
   - Work IQ (MCP) requires tenant admin setup (documented, graceful degradation)
   - SQL firewall IP discovery can fail (retry + strict mode option)
   - Multi-tenancy not yet supported (single-tenant per customer is MVP)
   - CI/CD pipelines need manual secret/federated identity setup (not auto-provisioned)

7. **Electric utility customer value proposition:**
   - **Identity-bound infrastructure:** Every resource auto-tagged with owner email + cost center (required for FERC/NERC audits)
   - **Policy-enforced generation:** Compliance is "shift-left" (checked before deployment, not after)
   - **Audit trail:** Non-repudiation in SQL (who deployed what, when, whether approved)
   - **Cost transparency:** Pre-deployment estimates + post-deployment chargeback by BU
   - **Template reuse:** Security/networking best practices encoded in pre-approved modules

8. **Action items before customer pitch:**
   - Run setup.ps1 end-to-end in your subscription (test all 9 steps)
   - Document post-setup checklist (Entra ID consent, Work IQ setup, firewall strict mode)
   - Create customer-facing narrative: identity + policy + cost as 3-pillar story
   - Develop compliance fact sheets: governance, audit trail, security standards
   - Package deployment script for customer consumption (setup.ps1 + requirements + runbook)

**Recommendation:** Proceed with tenant deployment confidence. Identity model and governance architecture are enterprise-grade. Electric utilities will recognize the compliance rigor.

