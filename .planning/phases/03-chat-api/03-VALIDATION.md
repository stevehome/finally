# Phase 03: Chat API — Validation Architecture

## Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3+ with pytest-asyncio 0.24+ |
| Config file | `backend/pyproject.toml` (`[tool.pytest.ini_options]`) |
| Quick run command | `uv run --extra dev pytest tests/test_chat.py -v` |
| Full suite command | `uv run --extra dev pytest -v` |

## Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CHAT-01 | POST /api/chat returns 200 with message field | unit | `pytest tests/test_chat.py::test_chat_returns_message -x` | No — Wave 0 |
| CHAT-02 | Response reflects current portfolio state | unit | `pytest tests/test_chat.py::test_chat_includes_portfolio_context -x` | No — Wave 0 |
| CHAT-03 | Trade in LLM response auto-executed | unit | `pytest tests/test_chat.py::test_chat_auto_executes_trade -x` | No — Wave 0 |
| CHAT-04 | Watchlist add/remove from LLM response applied | unit | `pytest tests/test_chat.py::test_chat_applies_watchlist_changes -x` | No — Wave 0 |
| CHAT-05 | History from prior calls included in LLM messages | unit | `pytest tests/test_chat.py::test_chat_history_persisted -x` | No — Wave 0 |
| CHAT-06 | LLM_MOCK=true returns deterministic response | unit | `pytest tests/test_chat.py::test_chat_mock_mode -x` | No — Wave 0 |
| CHAT-07 | Trade validation failure in response, not HTTP 400 | unit | `pytest tests/test_chat.py::test_chat_failed_trade_in_response -x` | No — Wave 0 |

## Sampling Rate
- **Per task commit:** `uv run --extra dev pytest tests/test_chat.py -v`
- **Per wave merge:** `uv run --extra dev pytest -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

## Wave 0 Gaps
- [ ] `tests/test_chat.py` — covers CHAT-01 through CHAT-07
- [ ] All tests use `LLM_MOCK=true` via monkeypatch to avoid real API calls
