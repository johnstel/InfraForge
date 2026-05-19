# Inara History

## Seed Context

- **Project:** InfraForge
- **Requested by:** John Stelmaszek
- **Description:** Self-service infrastructure platform for enterprise teams to provision production-ready Azure infrastructure from natural language while platform teams retain governance through approved templates, service approvals, policies, cost transparency, and deployment validation.
- **Stack:** FastAPI/Python 3.13 backend, Azure SQL Database, GitHub Copilot SDK, Microsoft Entra ID, Microsoft Graph, Microsoft Work IQ MCP, Fabric IQ, vanilla JavaScript SPA, ARM SDK deployment engine.

## Learnings

### Session 1: Utility Customer Strategy & Go-to-Market (Comprehensive Analysis)

**Context**: Inara (Customer Strategy Lead) requested a comprehensive go-to-market plan targeting Electric Energy organizations (Consumers Energy, utilities) with focus on grounding all positioning in actual product capabilities.

**Approach**:
- Examined foundational docs (ARCHITECTURE.md, README.md, TECHNICAL.md, SETUP.md, UI_STYLE_GUIDE.md)
- Reviewed existing squad decisions: Kaylee's Azure deployment plan (cost, infrastructure, setup script), Zoe's security/governance plan (compliance narrative, identity-driven tagging, FERC/NERC alignment draft)
- Reviewed existing artifacts: DEMO_GUIDE.md (12-step pipeline), VIDEO_SCRIPT.md, presentations/InfraForge.pptx
- Synthesized into comprehensive presentation plan with positioning, demo walkthrough, objection handling, pilot packaging, and validation claims

**Key Discoveries**:

1. **Deployment Model**: Deploy-in-customer-tenant (not SaaS)
   - Each customer gets their own InfraForge instance in their Azure subscription
   - Minimal baseline: ~$13/mo (SQL Basic ~$5 + App Service B1 ~$8)
   - Setup via PowerShell script: 20–30 minutes, mostly unattended
   - Kaylee's deployment plan is definitive reference for tenant architecture, resource layout, env vars, prerequisites, cost breakdown, SQL firewall strategy

2. **Utility-Specific Value Drivers** (grounded in actual capabilities):
   - **Governance & Compliance**: Identity-driven tagging auto-populates owner, cost center, department from Entra ID claims; policy-driven generation enforces rules at generation time (shift-left compliance); all decisions logged to SQL
   - **Cost Transparency**: Cost estimates shown before deployment; optional Fabric IQ analytics dashboard rolls up costs by cost center/department
   - **Auditability at Every Step**: Chat → governance check → generation → cost validation → approval → What-If → deployment → audit trail (all logged with timestamp, user, outcome)
   - **Self-Service without Loss of Control**: Approved template catalog + policy engine + service approval gates enable app teams to provision without tickets while platform teams maintain governance

3. **Demo Story Arc** (from DEMO_GUIDE.md, 12-step pipeline):
   - Natural language request → governance validation → template catalog search → cost estimate → generation (Bicep) → approval (if not template) → What-If preview → ARM deployment → audit trail
   - Key audience hook: Policy-enforced generation at *request time*, not post-deployment bolting-on
   - Compelling for utilities: Every step logged (request, policy check, estimate, approval, deployment outcome)

4. **Key Adoption Blockers** (requiring team validation before customer sale):
   - **Copilot SDK licensing** (BLOCKING): Can customers legally run Copilot SDK agents in their own tenants? Is there a licensing model, or must they have their own Copilot subscriptions? **Needs Mal validation**
   - **GitHub requirement**: Assumed customers have GitHub orgs. What if customer uses GitLab or has GitHub resistance? **Needs Mal clarification (is GitHub pluggable?)**
   - **Fabric IQ recommendation**: Zoe marks as optional, but if cost analytics dashboards require it, ROI conversation changes. Is Fabric truly optional or should we recommend as table stakes? What's the minimum SKU and cost? **Needs Kaylee clarification**
   - **Work IQ stability**: Is Work IQ production-ready or should we gate as beta? Does it work in sovereign clouds? **Needs Mal/Microsoft validation**
   - **FERC/NERC compliance alignment**: System claims to help with compliance (tagging, audit trails, policy enforcement), but line-by-line alignment against actual FERC/NERC standards is unvalidated. **Needs Zoe regulatory alignment review before customer use**

5. **Non-Obvious Behaviors** (from reading code/docs):
   - Group claims in Entra ID are optional but required for RBAC-driven role assignment; customers without group claims need manual role assignment in app
   - Managed identities configured per-deployment context (local Azure CLI, managed identity in cloud) — DefaultAzureCredential handles all cases transparently
   - Policy-driven generation: policies enforce rules at template generation time, not post-deployment (shift-left compliance, no exceptions)
   - SQL firewall auto-provisioned at startup (queries public IP, adds rule with backoff retry) — reliability story and security story (automatic, not user error)

**Outputs Created**:
- `.squad/decisions/inbox/inara-customer-presentation-plan.md` — Comprehensive 8,000+ word customer strategy document containing:
  - Executive summary (governance + self-service + auditability value prop)
  - Positioning & messaging (core value prop, utility angle with concrete examples)
  - Presentation outline (5-slide structure: problem → solution → architecture → demo → objection handling)
  - 12-step demo walkthrough (from DEMO_GUIDE.md, utility-focused framing)
  - Utility-specific objection handling (with responses for each common concern)
  - Pilot packaging checklist (customer readiness, deployment sequence, success metrics, 4-week timeline)
  - Claims requiring validation (6 critical claims with specific questions for each team member)
  - Customer communication templates (outreach email, pre-demo checklist, post-demo pilot proposal)
  - Sales metrics & tracking (conversation history, indicators of interest, closure indicators)
  - Appendices: file references, one-page elevator pitch, closing checklist

**Critical Next Steps** (Blocking for Customer Use):
1. **Mal** validates Copilot SDK licensing model (can customers run agents in their tenants? per-user cost? per-deployment cost?)
2. **Zoe** confirms FERC/NERC compliance mapping (line-by-line alignment of tagging, audit logs, policy enforcement to specific FERC/NERC requirements)
3. **Kaylee** clarifies Fabric recommendation (optional or table stakes? minimum SKU cost? ROI threshold?)
4. **Mal** validates Work IQ production readiness and sovereign cloud support
5. **Mal** clarifies GitHub requirement (pluggable or hard-coded? GitLab alternative?)
6. **All team members** review and approve final customer-facing claims before first customer presentation

**Team Coordination**:
- Present comprehensive plan to squad at next standup
- Assign validation claims to specific team members (Mal: licensing, Work IQ, GitHub; Kaylee: Fabric recommendation; Zoe: FERC/NERC mapping)
- Set deadline for validation feedback (target: before customer outreach)
- Schedule sales team training on demo flow and objection handling once claims are validated

