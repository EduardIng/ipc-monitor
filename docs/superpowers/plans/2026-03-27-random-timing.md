# Random Timing Implementation Plan

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make each monitoring run fire at a random time within ±3 minutes of the scheduled 08:00/11:00/14:00/17:00 Prague time, so checks don't arrive at the exact same second every day.

**Architecture:** The GitHub Actions cron fires 3 minutes early. `monitor.py` sleeps a random 0–360 seconds at startup before doing any work. Net effect: each run lands uniformly at random in a 6-minute window centered on the target hour.

**Tech Stack:** Python `random`, `time` — no new dependencies.

---

## Why this approach

GitHub Actions cron cannot be randomized at the scheduler level — it always fires at a fixed UTC time. The standard solution is to fire early and sleep in the script:

| Step | What happens |
|------|-------------|
| Cron fires at HH:57 UTC (= target hour − 3 min) | Runner starts |
| `monitor.py` sleeps `random.randint(0, 360)` seconds | 0–6 min random delay |
| Actual check runs | Lands between HH:57 and HH+1:03 UTC = ±3 min of target |

Cron change: `57 4,7,10,13 * * *` UTC
- 04:57 UTC = 05:57 CET = 06:57 CEST → window 05:57–06:03 CET / 06:57–07:03 CEST

Wait — let me recalculate correctly:

Target Prague times: 08:00, 11:00, 14:00, 17:00
Prague winter (CET = UTC+1): target UTC = 07:00, 10:00, 13:00, 16:00
Fire 3 min early: 06:57, 09:57, 12:57, 15:57 UTC
Cron: `57 6,9,12,15 * * *`
Window: 06:57–07:03 UTC = 07:57–08:03 CET ✓

Prague summer (CEST = UTC+2): same cron fires at 08:57–09:03 CEST (target was 08:00, actual 09:00 ± 3 min) — same +1h DST drift as before, which is already accepted.

---

## Files

- Modify: `monitor.py` — add random sleep at start of `main()`
- Modify: `.github/workflows/monitor.yml` — change cron from `0 7,10,13,16` to `57 6,9,12,15`
- Modify: `tests/test_monitor_timing.py` — new test file verifying sleep is called

---

## Chunk 1: Implementation

### Task 1: Add random sleep to monitor.py

**Files:**
- Modify: `monitor.py`
- Create: `tests/test_monitor_timing.py`

The sleep goes at the very start of `main()`, before any logging or work. This way the runner starts up, then waits a random amount of time before the check begins.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_monitor_timing.py
import pytest
from unittest.mock import patch, call


def test_main_sleeps_random_amount(monkeypatch):
    """main() must call time.sleep() once with a value between 0 and 360."""
    sleep_calls = []
    monkeypatch.setattr("monitor.time.sleep", lambda s: sleep_calls.append(s))
    monkeypatch.setattr("monitor.load_cache", lambda: {})
    monkeypatch.setattr("monitor.run_check", lambda data: None)
    monkeypatch.setattr("monitor.save_cache", lambda data: None)

    import monitor
    monitor.main()

    assert len(sleep_calls) == 1, "Expected exactly one time.sleep() call"
    assert 0 <= sleep_calls[0] <= 360, f"Sleep must be 0–360s, got {sleep_calls[0]}"


def test_random_sleep_uses_randint(monkeypatch):
    """main() must use random.randint(0, 360) as the sleep value."""
    randint_calls = []

    def fake_randint(a, b):
        randint_calls.append((a, b))
        return 42

    monkeypatch.setattr("monitor.random.randint", fake_randint)
    monkeypatch.setattr("monitor.time.sleep", lambda s: None)
    monkeypatch.setattr("monitor.load_cache", lambda: {})
    monkeypatch.setattr("monitor.run_check", lambda data: None)
    monkeypatch.setattr("monitor.save_cache", lambda data: None)

    import monitor
    monitor.main()

    assert len(randint_calls) == 1
    assert randint_calls[0] == (0, 360), f"Expected randint(0, 360), got randint{randint_calls[0]}"
```

- [ ] **Step 2: Run the tests to confirm they fail**

```bash
cd ~/ipc-monitor && source venv/bin/activate && pytest tests/test_monitor_timing.py -v
```

Expected: FAIL — `monitor.main()` does not call `time.sleep()` yet.

- [ ] **Step 3: Add random sleep to `monitor.py`**

Add `import random` and `import time` to the imports at the top (both are stdlib — no new dependencies). Then add the sleep as the first line of `main()`:

```python
import random
import time  # already imported — ensure it's present
```

In `main()`:

```python
def main():
    delay = random.randint(0, 360)
    time.sleep(delay)
    logger.info("=" * 60)
    logger.info(f"IPC Monitor check started (delayed {delay}s)")
    ...
```

> **Note:** `time` is already imported in `monitor.py` (used in `check_with_retry` for `time.sleep(RETRY_PAUSE)`). Only `import random` needs to be added.

- [ ] **Step 4: Run the tests to confirm they pass**

```bash
pytest tests/test_monitor_timing.py -v
```

Expected: 2 tests pass.

- [ ] **Step 5: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add monitor.py tests/test_monitor_timing.py
git commit -m "feat: random ±3min delay at monitor startup"
```

---

### Task 2: Update cron in workflow and push

**Files:**
- Modify: `.github/workflows/monitor.yml`

Change the cron from `0 7,10,13,16 * * *` (fires on the hour) to `57 6,9,12,15 * * *` (fires 3 minutes before the hour). Combined with the 0–360s sleep, this produces a uniform ±3 minute window around each target time.

- [ ] **Step 1: Update the cron in `.github/workflows/monitor.yml`**

```yaml
on:
  schedule:
    - cron: "57 6,9,12,15 * * *"
  workflow_dispatch:
```

Add a comment explaining the timing:

```yaml
on:
  schedule:
    # Fire 3 min early; monitor.py sleeps random 0-360s → ±3 min jitter around target
    # UTC 06:57/09:57/12:57/15:57 = Prague 07:57–08:03 / 10:57–11:03 / ... (winter)
    - cron: "57 6,9,12,15 * * *"
  workflow_dispatch:
```

- [ ] **Step 2: Commit and push**

```bash
git add .github/workflows/monitor.yml
git commit -m "feat: fire cron 3min early to enable random timing window"
git push
```

- [ ] **Step 3: Trigger a manual run and verify the delay appears in the log**

```bash
gh workflow run monitor.yml --repo EduardIng/ipc-monitor
gh run watch --repo EduardIng/ipc-monitor
```

Then check the log:

```bash
gh run view --log --repo EduardIng/ipc-monitor | grep "delayed"
```

Expected: a line like `IPC Monitor check started (delayed 217s)` — confirming the random sleep fired.

---

## Timing Reference

| Cron fires (UTC) | Prague winter window | Prague summer window |
|------------------|---------------------|---------------------|
| 06:57 | 07:57–08:03 | 08:57–09:03 |
| 09:57 | 10:57–11:03 | 11:57–12:03 |
| 12:57 | 13:57–14:03 | 14:57–15:03 |
| 15:57 | 16:57–17:03 | 17:57–18:03 |
