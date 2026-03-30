---
phase: 2
slug: portfolio-watchlist-api
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-30
---

# Phase 2 — Validation Strategy

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
| 2-01-01 | 01 | 1 | PORT-01 | unit | `cd backend && uv run pytest tests/test_portfolio.py -x -q` | ❌ W0 | ⬜ pending |
| 2-01-02 | 01 | 1 | PORT-02 | unit | `cd backend && uv run pytest tests/test_portfolio.py::test_buy_trade -x -q` | ❌ W0 | ⬜ pending |
| 2-01-03 | 01 | 1 | PORT-03 | unit | `cd backend && uv run pytest tests/test_portfolio.py::test_sell_trade -x -q` | ❌ W0 | ⬜ pending |
| 2-01-04 | 01 | 1 | PORT-04 | unit | `cd backend && uv run pytest tests/test_portfolio.py::test_validation -x -q` | ❌ W0 | ⬜ pending |
| 2-01-05 | 01 | 1 | PORT-05 | unit | `cd backend && uv run pytest tests/test_portfolio.py::test_trade_history -x -q` | ❌ W0 | ⬜ pending |
| 2-01-06 | 01 | 1 | PORT-06 | unit | `cd backend && uv run pytest tests/test_portfolio.py::test_snapshot -x -q` | ❌ W0 | ⬜ pending |
| 2-02-01 | 02 | 1 | PORT-07 | unit | `cd backend && uv run pytest tests/test_portfolio.py::test_snapshot_background -x -q` | ❌ W0 | ⬜ pending |
| 2-02-02 | 02 | 1 | PORT-08 | unit | `cd backend && uv run pytest tests/test_portfolio.py::test_portfolio_history -x -q` | ❌ W0 | ⬜ pending |
| 2-03-01 | 03 | 2 | WATCH-01 | unit | `cd backend && uv run pytest tests/test_watchlist.py::test_get_watchlist -x -q` | ❌ W0 | ⬜ pending |
| 2-03-02 | 03 | 2 | WATCH-02 | unit | `cd backend && uv run pytest tests/test_watchlist.py::test_add_ticker -x -q` | ❌ W0 | ⬜ pending |
| 2-03-03 | 03 | 2 | WATCH-03 | unit | `cd backend && uv run pytest tests/test_watchlist.py::test_remove_ticker -x -q` | ❌ W0 | ⬜ pending |
| 2-03-04 | 03 | 2 | WATCH-04 | unit | `cd backend && uv run pytest tests/test_watchlist.py::test_add_starts_streaming -x -q` | ❌ W0 | ⬜ pending |
| 2-03-05 | 03 | 2 | WATCH-05 | unit | `cd backend && uv run pytest tests/test_watchlist.py::test_remove_stops_streaming -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `backend/tests/test_portfolio.py` — stubs for PORT-01 through PORT-08
- [ ] `backend/tests/test_watchlist.py` — stubs for WATCH-01 through WATCH-05
- [ ] Existing `backend/tests/conftest.py` with `tmp_db` fixture already covers DB isolation

*Existing pytest + pytest-asyncio infrastructure is already installed (84 tests passing from Phase 1).*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Background snapshot runs every 30s | PORT-07 | Time-based task; fast unit test would use fake clock | Start app, wait 35s, check portfolio_snapshots table has new rows |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
