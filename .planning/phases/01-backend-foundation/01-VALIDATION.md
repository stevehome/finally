---
phase: 1
slug: backend-foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-30
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3+ with pytest-asyncio 0.24+ |
| **Config file** | `backend/pyproject.toml` |
| **Quick run command** | `cd backend && uv run pytest tests/ -x -q` |
| **Full suite command** | `cd backend && uv run pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `cd backend && uv run pytest tests/ -x -q`
- **After every plan wave:** Run `cd backend && uv run pytest tests/ -v --tb=short`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-01 | 01 | 0 | BACK-01 | unit | `cd backend && uv run pytest tests/test_db.py -x -q` | ❌ W0 | ⬜ pending |
| 1-01-02 | 01 | 1 | BACK-02 | unit | `cd backend && uv run pytest tests/test_main.py -x -q` | ❌ W0 | ⬜ pending |
| 1-01-03 | 01 | 1 | BACK-03 | integration | `cd backend && uv run pytest tests/test_main.py::test_health -x -q` | ❌ W0 | ⬜ pending |
| 1-01-04 | 01 | 1 | BACK-04 | integration | `cd backend && uv run pytest tests/test_main.py::test_sse_stream -x -q` | ❌ W0 | ⬜ pending |
| 1-01-05 | 01 | 1 | BACK-05 | unit | `cd backend && uv run pytest tests/test_db.py::test_seed_data -x -q` | ❌ W0 | ⬜ pending |
| 1-01-06 | 01 | 1 | BACK-06 | unit | `cd backend && uv run pytest tests/test_db.py::test_watchlist_seed -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_db.py` — stubs for BACK-01, BACK-05, BACK-06 (DB init, seed data, watchlist)
- [ ] `backend/tests/test_main.py` — stubs for BACK-02, BACK-03, BACK-04 (app startup, health, SSE stream)
- [ ] `backend/tests/conftest.py` — shared fixtures (tmp db path, test client)

*Existing `backend/tests/` directory already has some test files; Wave 0 adds missing stubs only.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| SSE stream delivers live prices continuously | BACK-04 | Requires running app + EventSource | Start app, open browser console, `new EventSource('/api/stream/prices')`, verify events arrive |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
