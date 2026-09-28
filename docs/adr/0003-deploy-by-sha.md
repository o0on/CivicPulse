# ADR 0003: Deploy by Git Commit SHA

**Date:** 2026-09-26
**Status:** Accepted

## Context
In early development, Docker images were tagged with `:latest` and deployed to Kubernetes. However, this led to unpredictable deployments because Kubernetes caches the `:latest` image, and rolling back to a previous state is difficult when the tag is constantly overwritten.

## Decision
We decided to tag all Docker images with the unique Git commit SHA (e.g., `backend:a1b2c3d`) and update the Kubernetes manifests to deploy this specific SHA.

## Rationale
1. **Traceability:** We can look at the running pods and instantly know exactly which Git commit is deployed in the environment.
2. **Reliable Rollbacks:** Because images are immutable, rolling back is as simple as reverting the deployment to point to an older SHA. The image is guaranteed to be the exact state of the code at that time.
3. **Idempotency:** Applying a manifest with a specific SHA guarantees the desired state. Applying `:latest` might trigger a pull, or it might not, depending on the node's `imagePullPolicy`.

## Consequences
- **Positive:** Highly reliable, reproducible, and traceable deployments.
- **Negative:** The CD pipeline is slightly more complex, requiring Kustomize or sed to dynamically inject the SHA into the manifest during the GitHub Actions workflow.
