---
phase: 06-docker-deployment
plan: 3
status: complete
---

# Summary: Phase 06-03 — Start/Stop Scripts

## What Was Done

Created four start/stop convenience scripts and validated the Docker image with a smoke test.

## Artifacts Created

- `scripts/start_mac.sh` — executable; idempotently removes any existing `finally` container, builds image if absent or `--build` passed, runs `docker run -d` with `finally-data:/app/db` volume, port `8000:8000`, `--env-file .env`, prints URL, opens browser
- `scripts/stop_mac.sh` — executable; `docker stop finally && docker rm finally`, volume preserved
- `scripts/start_windows.ps1` — PowerShell equivalent of start_mac.sh with `param([switch]$Build)`
- `scripts/stop_windows.ps1` — PowerShell equivalent of stop_mac.sh, no volume removal

## Smoke Test Result

```
docker run -d --name finally-smoke -e LLM_MOCK=true -p 8001:8000 finally
curl -sf http://localhost:8001/api/health
{"status":"ok","db":"ok","market_data":"running"}
```

Health endpoint returned `{"status":"ok"}`. Container subsequently stopped and removed.

## Commit

`e72e098` — feat(docker): add start/stop scripts for macOS and Windows

## Success Criteria

- [x] scripts/start_mac.sh created and chmod +x
- [x] scripts/stop_mac.sh created and chmod +x
- [x] scripts/start_windows.ps1 created
- [x] scripts/stop_windows.ps1 created
- [x] start_mac.sh: docker rm -f finally (idempotent), docker run -d with volume and env-file, prints URL, opens browser
- [x] stop_mac.sh: docker stop && docker rm, no volume removal
- [x] Smoke test passed: /api/health returned {"status":"ok"}
- [x] All scripts committed with --no-verify
