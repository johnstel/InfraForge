# Wash History

## Seed Context

- **Project:** InfraForge
- **Requested by:** John Stelmaszek
- **Description:** Self-service infrastructure platform for enterprise teams to provision production-ready Azure infrastructure from natural language while platform teams retain governance through approved templates, service approvals, policies, cost transparency, and deployment validation.
- **Stack:** FastAPI/Python 3.13 backend, Azure SQL Database, GitHub Copilot SDK, Microsoft Entra ID, Microsoft Graph, Microsoft Work IQ MCP, Fabric IQ, vanilla JavaScript SPA, ARM SDK deployment engine.

## Learnings

### Session: Readiness Validation Plan (2026-05-14)

**Key Findings:**
1. **Test Coverage Asymmetry** — Infrastructure tests exist (20+ Azure resource checks) but core API has zero endpoint tests despite 137 route handlers. Copilot SDK integration completely untested. This is highest risk for regressions.

2. **Setup Script is Production-Ready** — `scripts/setup.ps1` is comprehensive: 9 steps, preflight checks, fallback region logic, credential lifetime policy handling, idempotent .env merge. No equivalent exists for Linux/macOS (blocker for cloud-native pilot).

3. **Demo is Fragile Without E2E Test** — DEMO_GUIDE.md is clear but there's no automated test for "catalog sync → onboard vnet → verify resources." Each live demo is a coin flip on SQL connection, firewall, or token expiry.

4. **Critical Gaps for Customer Pilot:**
   - No Docker/container support → can't deploy to Kubernetes (Consumers Energy will ask for this)
   - No load test → concurrent pipeline performance unknown (5+ users will break it)
   - Fabric IQ and Work IQ mentioned but not validated in production
   - GitHub Actions CI/CD incomplete (SWA only, no API deployment)

5. **SQL Firewall Auto-Remediation Works** — `test_sql_firewall.py` validates IP extraction and retry logic; setup script detects and updates firewall. This is solid.

6. **Documentation Good, Runbooks Missing** — ARCHITECTURE.md and SETUP.md are excellent references, but troubleshooting runbooks are absent. Customer support will struggle with "SQL firewall blocked" or "token expired" scenarios.

**Actionable Recommendations:**
- **MUST DO before customer pilot:** Add Docker, E2E test, load test, 3 runbooks
- **SHOULD DO:** Add API endpoint tests, Work IQ validation, demo data reset script
- **NICE TO HAVE:** Dark mode, mobile UI testing, rollback documentation

**Validation Decision:** Recommend internal 1-week pilot before customer handoff to catch hidden bugs under realistic load.

