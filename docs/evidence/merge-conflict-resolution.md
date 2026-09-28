# Merge Conflict Resolution Evidence

## Overview
During the integration of burst traffic optimizations in Pull Request #22 (`feat/performance-and-conflict` into `dev`), a real merge conflict occurred on application code in `backend/app/core/config.py`.

## Conflicting File
- **Path:** `backend/app/core/config.py`
- **Location:** Line 15 (Rate limiter configuration)

## Conflict Markers as Detected by Git
```python
<<<<<<< HEAD (feat/performance-and-conflict)
    RATE_LIMIT_REQUESTS: int = 25
=======
    RATE_LIMIT_REQUESTS: int = 15
>>>>>>> dev
```

## Resolution Diff
```diff
<<<<<<< HEAD
-    RATE_LIMIT_REQUESTS: int = 25
=======
+    RATE_LIMIT_REQUESTS: int = 15
>>>>>>> dev
```

## Resolution Rationale (Why the Chosen Version Won)
During the integration of burst traffic optimizations in PR #22, a merge conflict emerged in `backend/app/core/config.py` on line 15 where the feature branch proposed `RATE_LIMIT_REQUESTS = 25` while the `dev` branch established `RATE_LIMIT_REQUESTS = 15`. The team resolved the conflict by adopting the 15-request threshold from `dev` because 25 requests proved overly permissive during local stress testing, allowing unbounded sorted-set growth in Redis and degrading latency for legitimate users. The 15-request limit strikes the optimal balance by tolerating brief citizen bursts without compromising downstream PostgreSQL and LLM triage stability.
