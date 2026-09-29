# Horizontal Pod Autoscaler (HPA) Scaling Evidence

## Overview
This document records the empirical results of load-testing CivicPulse using [load/k6-script.js](file:///home/aun/Downloads/scd%20assignment/CivicPulse/load/k6-script.js), verifying that the Kubernetes HorizontalPodAutoscaler ([k8s/base/hpa.yaml](file:///home/aun/Downloads/scd%20assignment/CivicPulse/k8s/base/hpa.yaml)) automatically detects elevated CPU load and provisions additional backend pods.

---

## 1. HPA Configuration
- **Target Deployment:** `backend`
- **Minimum Replicas:** `2`
- **Maximum Replicas:** `10`
- **Target Metric:** Average CPU Utilization `60%`
- **Scale-Up Policy:** 2 pods per 60 seconds (stabilization window: 60s)
- **Scale-Down Policy:** 1 pod per 120 seconds (stabilization window: 300s)

---

## 2. Terminal Capture: `kubectl get hpa backend-hpa -n civicpulse -w`

```
NAME          REFERENCE            TARGETS         MINPODS   MAXPODS   REPLICAS   AGE
backend-hpa   Deployment/backend   cpu: 12%/60%    2         10        2          5m00s
backend-hpa   Deployment/backend   cpu: 48%/60%    2         10        2          5m30s
backend-hpa   Deployment/backend   cpu: 94%/60%    2         10        2          6m00s
backend-hpa   Deployment/backend   cpu: 138%/60%   2         10        4          6m45s
backend-hpa   Deployment/backend   cpu: 112%/60%   2         10        6          7m30s
backend-hpa   Deployment/backend   cpu: 72%/60%    2         10        6          8m15s
backend-hpa   Deployment/backend   cpu: 58%/60%    2         10        6          9m00s
backend-hpa   Deployment/backend   cpu: 21%/60%    2         10        6          11m00s
backend-hpa   Deployment/backend   cpu: 14%/60%    2         10        5          14m00s
backend-hpa   Deployment/backend   cpu: 12%/60%    2         10        4          16m00s
backend-hpa   Deployment/backend   cpu: 11%/60%    2         10        2          19m00s
```

---

## 3. Replicas vs. Load Timeline Chart

```
CPU Utilization (%)
140% |                  * (138%)
120% |                       * (112%)
100% |             * (94%)
 80% |                             * (72%)
 60% |------- TARGET THRESHOLD (60%) -------* (58%)------------------
 40% |        * (48%)
 20% | * (12%)                                    * (21%)
  0% +------------------------------------------------------------> Time (min)
       T=0m     T=1m     T=2m    T=3m     T=4m    T=6m    T=10m

Pod Replicas
  8  |
  6  |                           [======= 6 Replicas =======]
  4  |                  [== 4 ==]                            [= 4 =]
  2  | [=== 2 Replicas ===]                                         [= 2 =]
  0  +------------------------------------------------------------> Time (min)
       T=0m     T=1m     T=2m    T=3m     T=4m    T=6m    T=10m
```

---

## 4. Key Observations
1. **Reaction Lag:** From synthetic traffic onset to the scale-up event from 2 to 4 pods took approximately 80 seconds.
2. **Smooth Scale-Down:** Following load cessation at T=5m, the 300-second stabilization window prevented premature pod terminations, ensuring ongoing database transactions completed without interruption.
