---
phase: 04-frontend-shell-watchlist
plan: 01
subsystem: ui
tags: [nextjs, tailwind, typescript, static-export, fastapi]

requires:
  - phase: 03-chat-api
    provides: FastAPI backend with all API routes and static file serving configured in main.py
provides:
  - Next.js 16 project scaffolded in frontend/ with TypeScript, Tailwind v4, ESLint, App Router
  - Static export configured with distDir pointing to backend/static/
  - Dark terminal theme via Tailwind v4 @theme block (project colors + flash animations)
  - Root layout and placeholder page ready for plan 04-02
  - backend/static/index.html built and ready for FastAPI to serve
affects: [04-02, 04-03, 04-04, 04-05, Dockerfile]

tech-stack:
  added:
    - Next.js 16.2.1 (TypeScript, App Router, static export)
    - Tailwind CSS v4 with @tailwindcss/postcss
    - lightweight-charts 5.1.0
  patterns:
    - Tailwind v4 CSS-only config via @theme block in globals.css (no tailwind.config.js)
    - distDir: ../backend/static routes Next.js build directly to FastAPI static mount
    - Flash animations (.flash-up, .flash-down) defined globally for use in watchlist rows

key-files:
  created:
    - frontend/package.json
    - frontend/next.config.ts
    - frontend/postcss.config.mjs
    - frontend/tsconfig.json
    - frontend/eslint.config.mjs
    - frontend/app/globals.css
    - frontend/app/layout.tsx
    - frontend/app/page.tsx
  modified:
    - .gitignore (added backend/static/ exclusion)

key-decisions:
  - "Tailwind v4 uses CSS-only @theme config — no tailwind.config.js needed or created"
  - "distDir: ../backend/static routes build output directly to FastAPI static mount point"
  - "backend/static/ added to .gitignore — build output should not be committed"

patterns-established:
  - "Tailwind v4: custom colors defined as --color-* in @theme block, referenced as bg-bg-primary, text-text-muted etc."
  - "Flash animations defined once in globals.css, applied via className toggle in components"

requirements-completed: [FE-01, FE-02]

duration: 8min
completed: 2026-03-31
---

# Phase 4 Plan 1: Frontend Shell Summary

**Next.js 16 static export scaffolded with Tailwind v4 dark terminal theme; build outputs to backend/static/ where FastAPI serves it on port 8000**

## Performance

- **Duration:** ~8 min
- **Started:** 2026-03-31T14:37:00Z
- **Completed:** 2026-03-31T14:45:04Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- Next.js 16.2.1 project initialized with TypeScript, Tailwind v4, ESLint, App Router
- Static export configured with distDir pointing to ../backend/static (FastAPI serves from there)
- Dark terminal theme applied via Tailwind v4 @theme block with all project colors
- Flash animations (.flash-up, .flash-down) defined globally for price tick effects in plan 04-03
- Build succeeds: backend/static/index.html generated and ready for FastAPI

## Task Commits

1. **Task 1: Initialize Next.js project and configure static export** - `5fc80fa` (feat)
2. **Task 2: Apply dark terminal theme and scaffold root layout** - `62ec727` (feat)

## Files Created/Modified

- `frontend/package.json` - Next.js 16, Tailwind v4, lightweight-charts dependencies
- `frontend/next.config.ts` - output: export, distDir: ../backend/static, images.unoptimized
- `frontend/postcss.config.mjs` - @tailwindcss/postcss plugin (Tailwind v4 pattern)
- `frontend/tsconfig.json` - TypeScript config
- `frontend/app/globals.css` - Tailwind v4 @theme block with project colors + flash keyframes
- `frontend/app/layout.tsx` - FinAlly metadata, dark body background
- `frontend/app/page.tsx` - Minimal placeholder ("FinAlly — Loading...")
- `.gitignore` - Added backend/static/ exclusion

## Decisions Made

- Tailwind v4 uses CSS-only @theme config — no tailwind.config.js created (would conflict with v4)
- distDir: ../backend/static routes build directly to FastAPI's static file mount
- backend/static/ gitignored as build output (deviation Rule 2)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added backend/static/ to .gitignore**
- **Found during:** Task 2 (build verification)
- **Issue:** Plan didn't specify gitignoring the build output directory; generated files should not be committed
- **Fix:** Added `backend/static/` entry to root .gitignore
- **Files modified:** .gitignore
- **Verification:** git status shows backend/static/ not tracked
- **Committed in:** 62ec727 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (missing critical)
**Impact on plan:** Gitignore fix prevents accidental commit of build artifacts. No scope creep.

## Issues Encountered

None - build succeeded on first attempt. Tailwind v4 was already installed by create-next-app.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Frontend shell ready: dark theme, build pipeline, all project colors defined
- Flash animations ready for watchlist row components (plan 04-03)
- FastAPI already configured to serve backend/static/ (main.py StaticFiles mount is conditional on dir existing)
- Plan 04-02 can now build the full trading terminal layout on this foundation

---
*Phase: 04-frontend-shell-watchlist*
*Completed: 2026-03-31*
