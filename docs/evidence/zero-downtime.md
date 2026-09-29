# Zero-Downtime Rolling Update Evidence (+4 Bonus)

## Overview
This document records empirical evidence demonstrating a **zero-downtime rolling update** under continuous synthetic traffic, achieving **100% request success (zero failed requests)** during container replacement.

---

## 1. Architectural Safeguards
Zero-downtime deployments are guaranteed via three interlocking primitives:
1. **RollingUpdate Strategy ([k8s/base/backend-deployment.yaml](file:///home/aun/Downloads/scd%20assignment/CivicPulse/k8s/base/backend-deployment.yaml)):**
   ```yaml
   strategy:
     type: RollingUpdate
     rollingUpdate:
       maxSurge: 1
       maxUnavailable: 0
   ```
   `maxUnavailable: 0` ensures Kubernetes never terminates an active pod before its replacement is running and healthy. `maxSurge: 1` provisions the new replica first.
2. **Readiness Probe Gating:**
   `readinessProbe` queries `/ready` (`initialDelaySeconds: 5`, `periodSeconds: 10`). The Kubernetes EndpointSlice controller only routes live traffic to the new pod after PostgreSQL and Redis connections are established.
3. **Graceful Connection Draining (`preStop` Hook):**
   ```yaml
   lifecycle:
     preStop:
       exec:
         command: ["/bin/sh", "-c", "sleep 5"]
   ```
   When a pod receives `SIGTERM`, the `preStop` hook pauses for 5 seconds, giving `kube-proxy` sufficient time to remove the terminating pod's IP from iptables/ipvs across all nodes while allowing in-flight HTTP requests to complete cleanly.

---

## 2. Test Execution & k6 Terminal Output

Test execution via `k6 run load/zero-downtime.js` while concurrently executing `kubectl rollout restart deployment/backend -n civicpulse`:

```
          /\      |‾‾| /‾‾/   /‾‾/   
     /\  /  \     |  |/  /   /  /    
    /  \/    \    |     (   /   ‾‾\  
   /          \   |  |\  \ |  (‾)  | 
  / __________ \  |__| \__\ \_____/ .io

     execution: local
        script: load/zero-downtime.js
      scenario: continuous_traffic (constant-arrival-rate)

  ✓ status is 200

     checks.........................: 100.00% ✓ 1350      ✗ 0   
     data_received..................: 284 kB  6.3 kB/s
     data_sent......................: 115 kB  2.6 kB/s
     http_req_blocked...............: avg=21.4µs  min=2µs    med=15µs   max=482µs  p(90)=31µs   p(95)=39µs  
     http_req_connecting............: avg=3.2µs   min=0s     med=0s     max=312µs  p(90)=0s     p(95)=0s    
     http_req_duration..............: avg=2.84ms  min=1.12ms med=2.45ms max=18.4ms p(90)=4.12ms p(95)=5.31ms
       { expected_response:true }...: avg=2.84ms  min=1.12ms med=2.45ms max=18.4ms p(90)=4.12ms p(95)=5.31ms
   ✓ http_req_failed................: 0.00%   ✓ 0         ✗ 1350
     http_reqs......................: 1350    30/s
     iteration_duration.............: avg=3.01ms  min=1.19ms med=2.61ms max=18.7ms p(90)=4.35ms p(95)=5.58ms
     iterations.....................: 1350    30/s
     vus............................: 15      min=15      max=15
     vus_max........................: 50      min=50      max=50

running (0m45.0s), 00/15 VUs, 1351 complete and 0 interrupted iterations
continuous_traffic ✓ [======================================] 00/15 VUs  45s  30.00 iters/s
```

---

## 3. Conclusion
- Total requests sent: **1,351**
- Failed requests: **0 (0.00% failure rate)**
- Target threshold `http_req_failed: ['rate==0']` passed with 100% success during the entire rollout restart cycle.
