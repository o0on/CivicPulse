# GitOps Architecture & Argo CD Reconciliation (+4 Bonus)

## Overview
CivicPulse implements **Level 4 CI/CD Maturity** using **GitOps** principles. Rather than relying on push-based deployments from external CI runners (which require embedding long-lived cluster credentials inside GitHub Secrets), an in-cluster **Argo CD** controller continuously reconciles the cluster's state directly against the Git repository.

---

## 1. Argo CD Application Manifest
The declarative application configuration is defined in [`gitops/argocd-application.yaml`](file:///home/aun/Downloads/scd%20assignment/CivicPulse/gitops/argocd-application.yaml):

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: civicpulse-staging
  namespace: argocd
spec:
  project: default
  source:
    repoURL: 'https://github.com/o0on/CivicPulse.git'
    targetRevision: main
    path: k8s/overlays/prod
  destination:
    server: 'https://kubernetes.default.svc'
    namespace: civicpulse
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

---

## 2. Operational Workflow
```
Developer Commit ──> PR Check (CI) ──> Merge to main
                                             │
                                   GitHub Actions CD
                                (Builds & Pushes SHA Image)
                                             │
                                Updates k8s/overlays/prod
                                             │
                                    ┌────────┴────────┐
                                    ▼                 ▼
                             Git Repository       Argo CD Controller
                             (Single Source) <── (Polls repo every 3m)
                                                      │
                                             Reconciles & Deploys
                                                      ▼
                                              Kubernetes Cluster
```

1. **Continuous Reconciliation (`selfHeal: true`):**
   If an administrator or attacker manually alters a deployment configuration directly via `kubectl` (e.g., changes replica counts or environment variables), Argo CD immediately detects cluster drift and reverts the cluster back to the exact declared Git configuration.
2. **Automated Resource Pruning (`prune: true`):**
   When manifests or configuration objects are removed from Git, Argo CD automatically deletes the orphaned resources from the Kubernetes cluster.
3. **Pull-Based Security Model:**
   The cluster maintains zero inbound firewall holes. The Argo CD controller runs within the cluster and pulls configuration changes securely via HTTPS.

---

## 3. Deployment Procedure
To deploy Argo CD and reconcile CivicPulse:
```bash
# 1. Install Argo CD operator
kubectl create namespace argocd
kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml

# 2. Apply CivicPulse GitOps Application
kubectl apply -f gitops/argocd-application.yaml

# 3. Verify sync status
argocd app get civicpulse-staging
```
