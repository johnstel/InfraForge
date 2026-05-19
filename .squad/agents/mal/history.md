# Mal History

## Seed Context

- **Project:** InfraForge
- **Requested by:** John Stelmaszek
- **Description:** Self-service infrastructure platform for enterprise teams to provision production-ready Azure infrastructure from natural language while platform teams retain governance through approved templates, service approvals, policies, cost transparency, and deployment validation.
- **Stack:** FastAPI/Python 3.13 backend, Azure SQL Database, GitHub Copilot SDK, Microsoft Entra ID, Microsoft Graph, Microsoft Work IQ MCP, Fabric IQ, vanilla JavaScript SPA, ARM SDK deployment engine.

## Learnings

### 2026-05-14 — Repository Architecture Assessment

- **Stack confirmed:** FastAPI 3.13 + Azure SQL + Copilot SDK + Entra ID + vanilla JS SPA. No build step for frontend.
- **Key entry points:** `web_start.py` (web), `start.py` (CLI). Server runs on port 8080 via uvicorn.
- **Database:** All state in Azure SQL. Schema auto-creates via `init_db()` in `database.py`. Uses pyodbc + AAD token auth. ODBC Driver 18 required.
- **Setup script:** `scripts/setup.ps1` is PowerShell-only (Windows/winget). Handles SQL, Entra ID, RBAC, GitHub, Fabric, Python venv, and SQL connectivity test. Not usable for Linux cloud deployment — need separate Bicep/ARM.
- **CI/CD exists:** `.github/workflows/deploy-swa.yml` deploys the landing page (`infraforge-deploy/`) to Azure Static Web Apps. No workflow yet for the main app.
- **Catalog templates:** 6 Bicep files in `catalog/bicep/` (app-service, sql-db, key-vault, log-analytics, storage, three-tier-web blueprint). Seeded into DB.
- **Presentations:** Existing PPTX + HTML presentation in `presentations/`. Playbook in `PRESENTATION_PLAYBOOK.md` targets hackathon judges — needs adaptation for customer audiences.
- **Demo guide:** `DEMO_GUIDE.md` walks through the full product flow (sync → onboard → generate → deploy). Good basis for customer demo.
- **Deployment decision:** Recommended App Service Linux for John's tenant. Deploy-in-their-tenant model for electric utility customers.
- **Key risk:** Copilot SDK licensing in customer tenants is the biggest open question for customer adoption.
- **File sizes:** `src/web.py` ~9800 LOC, `static/app.js` ~14800 LOC, `static/styles.css` ~16400 LOC, `src/database.py` ~4600 LOC.

