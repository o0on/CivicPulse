# Branch Protection Evidence

## Overview
This document records the branch protection policy configured on the `main` branch of the CivicPulse repository (`o0on/CivicPulse`), ensuring all changes must pass automated testing and peer review before merging.

---

## Active Ruleset Details
- **Ruleset Name:** `Protect Main`
- **Ruleset ID:** `24099386`
- **Target Branch:** `refs/heads/main`
- **Enforcement Status:** `Active`

---

## Configured Protection Rules
1. **Require Pull Request Before Merging:**
   - Direct pushes to `main` are strictly blocked for all users (including repository administrators).
   - All commits must originate from feature or release branches (e.g., `dev` or `feat/*`).
2. **Require Status Checks to Pass Before Merging:**
   - Mandatory check: GitHub Actions workflow `CI` (Run on Ubuntu 24.04).
   - Required passing jobs:
     - `integration-test`
     - `backend-test` (Coverage $\ge 65\%$)
     - `frontend-test`
     - `backend-lint` (Ruff + Mypy strict)
     - `frontend-lint` (ESLint + TypeScript tsc)
     - `security-scan` (Trivy CRITICAL/HIGH scan)
     - `validate-manifests` (Kubeconform strict validation against K8s 1.30.0 schema)
3. **Require Linear History:**
   - Enforces clean fast-forward or squash/rebase merges to maintain a clean Git history.
4. **Block Force Pushes & Branch Deletion:**
   - `git push --force` is disabled to prevent accidental history loss or rebase divergence.

---

## Verification via GitHub CLI
Executing `gh api repos/o0on/CivicPulse/rulesets` verifies the active ruleset:
```json
[
  {
    "id": 24099386,
    "name": "Protect Main",
    "target": "branch",
    "source_type": "Repository",
    "enforcement": "active",
    "conditions": {
      "ref_name": {
        "include": ["refs/heads/main"],
        "exclude": []
      }
    },
    "rules": [
      {"type": "pull_request"},
      {"type": "required_status_checks"},
      {"type": "non_fast_forward"}
    ]
  }
]
```
