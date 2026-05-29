# Demo Secret Rotation Runbook

Use this runbook before every customer/demo cycle and any time credentials are exposed.

## Scope

Rotate and re-provision:
- `ENTRA_CLIENT_SECRET`
- `GITHUB_TOKEN`
- `INFRAFORGE_SESSION_SECRET`

## 1) Rotate credentials

### Entra app secret
1. Azure Portal → Entra ID → App registrations → InfraForge app.
2. Create a new client secret and record it in your approved secret manager.
3. Remove the previous secret after validation.

### GitHub token/PAT
1. Revoke the old token in GitHub settings.
2. Create a replacement token with minimum required scopes.
3. Store it only in your approved secret manager.

### Session secret
1. Generate a new high-entropy value (minimum 32 chars).
2. Update `INFRAFORGE_SESSION_SECRET` in secret manager.
3. Restart app instances so old sessions are invalidated.

## 2) Provision demo environment safely

1. Copy placeholder template: `Copy-Item .env.demo .env`
2. Inject runtime secrets from secret manager (never commit).
3. Confirm `.env` remains untracked: `git status --short`

## 3) Verify repository secret hygiene

Run from repo root:

```bash
git ls-files '.env' '.env.*'
git status --short
git grep -nE 'ghp_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{20,}|infraforge-dev-secret-change-in-prod' -- ':!docs/DEMO_SECRET_RUNBOOK.md'
```

Expected:
- only `.env.example` and `.env.demo` are tracked templates
- `.env` is not tracked
- no live secret values in tracked files

## 4) Demo handoff checklist

- [ ] Entra secret rotated
- [ ] GitHub token rotated
- [ ] Session secret rotated
- [ ] `.env` not tracked
- [ ] `.env.demo` placeholders preserved
