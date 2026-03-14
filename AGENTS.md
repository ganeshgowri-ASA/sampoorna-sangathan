# AGENTS.md - SampoornaSangathan Claude Code IDE Guide

## Sacred Principles
1. UNDERSTAND before coding - read context, PRD, existing code
2. ONE session = ONE feature branch = ONE module/fix
3. NEVER modify code outside your session scope
4. TEST every change before committing
5. ROLLBACK if tests fail - never force merge broken code

## PDCA Agile Cycle

### P (Plan)
- Read PRD in Notion: SampoornaSangathan PRD
- Check GitHub Issues for current sprint tasks
- Create feature branch: `feat/S{phase}.{session}-{description}`
- Define acceptance criteria before coding

### D (Do)
- Code the feature in isolated branch
- Follow monorepo structure: modules/{module-name}/
- Use shared packages: packages/ui, packages/db, packages/types
- Commit frequently with conventional commits

### C (Check)
- Run: `pnpm lint && pnpm typecheck && pnpm test`
- Verify Vercel preview deployment works
- Check Prisma schema compatibility with Railway PostgreSQL
- Test Odoo API connector if applicable
- Manual QA: verify UI, workflows, auth

### A (Act)
- Create PR to main with detailed description
- Review diff line-by-line
- Merge only if all checks pass
- Vercel auto-deploys on merge to main
- Tag release if milestone reached

## Integration Map

```
GitHub (sampoorna-sangathan)
  |-- push/merge --> Vercel (auto-deploy frontend)
  |-- push/merge --> GitHub Actions (CI: lint, test, typecheck)
  |-- Prisma migrate --> Railway PostgreSQL (database)
  |-- API calls --> Odoo (localhost:8069, WSL2 - ERP backend)
  |-- Claude Code IDE sessions (dev branches)
```

## Branch Strategy
- `main` - production (protected, auto-deploy to Vercel)
- `develop` - integration branch
- `feat/S{X}.{Y}-description` - feature branches
- `fix/description` - bug fixes
- `hotfix/description` - urgent production fixes

## Module Development Order
Phase 1: Core (Auth, Launchpad, UI Library, DB Schema)
Phase 2: Port Existing (KarmaDhara, SarvePratibha, KrayaVikrayam, Vidyalaya)
Phase 3: New Modules (Finance, Inventory, Projects, Communication)
Phase 4: Advanced (Asset Mgmt, E-Commerce, CMS, AI Integration)
Phase 5: Polish (API docs, i18n, monitoring)

## Environment Variables Required
- DATABASE_URL (Railway PostgreSQL)
- NEXTAUTH_SECRET
- NEXTAUTH_URL
- ANTHROPIC_API_KEY (Claude AI)
- ODOO_URL=http://localhost:8069
- ODOO_DB=sampoorna-sangathan
- ODOO_USER=admin@sampoornasangathan.com

## Odoo Integration
- Odoo 18 running on WSL2 at localhost:8069
- Database: sampoorna-sangathan
- Use XML-RPC/JSON-RPC API for data sync
- Modules to install: Accounting, Inventory, Purchase, Manufacturing
- Connector module bridges Odoo <-> Next.js via API

## Claude Code IDE Session Template
```
Session: S{X}.{Y} - {Description}
Branch: feat/S{X}.{Y}-{slug}
Scope: {module-name}
PRD Reference: Section {N}
Acceptance Criteria:
- [ ] Criterion 1
- [ ] Criterion 2
Dependencies: {list any}
Rollback Plan: git checkout main
```
