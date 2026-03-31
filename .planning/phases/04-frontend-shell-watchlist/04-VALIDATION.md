---
phase: 4
slug: frontend-shell-watchlist
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-31
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | No frontend unit test framework (E2E tests provide coverage per REQUIREMENTS.md) |
| **Config file** | none — Wave 0 scaffolds `package.json` |
| **Quick run command** | `cd frontend && npm run build` |
| **Full suite command** | `cd frontend && npm run build && npm run lint` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd frontend && npm run build`
- **After every plan wave:** Run `cd frontend && npm run build && npm run lint`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 4-01-01 | 01 | 1 | FE-01 | build | `cd frontend && npm run build` | ❌ W0 | ⬜ pending |
| 4-01-02 | 01 | 1 | FE-02 | build | `cd frontend && npm run build` | ❌ W0 | ⬜ pending |
| 4-02-01 | 02 | 1 | FE-04 | build | `cd frontend && npm run build` | ❌ W0 | ⬜ pending |
| 4-02-02 | 02 | 1 | FE-03 | build | `cd frontend && npm run build` | ❌ W0 | ⬜ pending |
| 4-03-01 | 03 | 2 | WUI-01 | build | `cd frontend && npm run build` | ❌ W0 | ⬜ pending |
| 4-03-02 | 03 | 2 | WUI-02..05 | build | `cd frontend && npm run build` | ❌ W0 | ⬜ pending |
| 4-04-01 | 04 | 3 | FE-01..04 | manual | browser smoke test | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `frontend/package.json` — scaffold via `npx create-next-app@latest`
- [ ] `frontend/next.config.ts` — needs `output: 'export'` + `distDir: '../backend/static'`
- [ ] `frontend/app/globals.css` — Tailwind v4 import + theme CSS variables
- [ ] `frontend/postcss.config.mjs` — `@tailwindcss/postcss` plugin

*Wave 0 is Plan 01 (Next.js scaffold). All other plans depend on it.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Dark theme colors applied | FE-02 | No automated color extraction | Load `http://localhost:8000`, verify bg ~#0d1117, accent #ecad0a |
| Header shows live portfolio value + cash | FE-03 | Requires live backend | Check header updates within 5s of page load |
| SSE stream connects | FE-04 | Requires running container | DevTools > Network > EventStream shows price events |
| Watchlist shows 10 tickers with sparklines | WUI-01..04 | Requires live backend | All 10 tickers visible, prices updating, sparklines growing |
| Price flash animation | WUI-05 | Visual CSS effect | Prices briefly flash green/red on change, fade ~500ms |
| Ticker click selects it | FE-02 | Visual interaction | Click ticker → highlighted state visible |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
