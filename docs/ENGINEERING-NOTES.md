# Engineering Notes

## 1. What was the hardest part of the assignment and how did you overcome it?
The most challenging part of the assignment was configuring the CI/CD pipeline to deploy specific Git SHAs rather than the `:latest` tag, while seamlessly passing this SHA from GitHub Actions into the Kubernetes manifests. I overcame this by leveraging Kustomize inside the CD pipeline (`.github/workflows/cd.yml`). By running `kustomize edit set image backend=myrepo/backend:${{ github.sha }}`, the pipeline updates the base manifest dynamically before running `kubectl apply -k`.

## 2. Explain your database architecture (schema, relationships).
We use PostgreSQL as the primary data store. The main table is `complaints`, which holds columns for `id`, `description`, `location_raw`, `contact_email`, and a timestamp. There is a secondary table `triage_results` linked via a foreign key `complaint_id`. It stores the LLM-extracted metadata: `category` (e.g., Infrastructure, Sanitation), `priority` (High/Medium/Low), and `extracted_location`. This separation cleanly isolates user-provided data from AI-generated metadata.

## 3. How did you verify the HPA works? Explain the lag.
I verified the Horizontal Pod Autoscaler (HPA) by running a k6 load test (`load/k6-script.js`). The script simulates a burst of users querying the stats endpoint and submitting complaints. 
There is a noticeable lag of approximately 90-120 seconds between the CPU spike and the new pods entering the `Running` state. This lag exists because the Metrics Server needs time to scrape and average the CPU metrics across the cluster (usually configured to a 1-minute window), and Kubernetes requires additional time to schedule the new pods and pull the container images.

## 4. Why does Vertical Pod Autoscaler (VPA) Off mode conflict with HPA on CPU?
If VPA is in `Auto` mode adjusting CPU requests, and HPA is also scaling based on CPU utilization percentage, they conflict. If HPA scales out due to high CPU, the VPA might simultaneously increase the CPU request of existing pods. This changes the denominator for HPA's percentage calculation, causing erratic scaling behavior (scale thrashing). Using VPA in `Off` mode solely for recommendations prevents this active conflict, allowing HPA to predictably scale horizontally.

## 5. What are the benefits of the Nginx proxy approach for the frontend?
By using Nginx to proxy API requests, the React frontend doesn't need to know the backend's absolute URL at build time. We serve the static React files from `/` and proxy any request matching `/api/` to the backend service. This eliminates the need for different build artifacts per environment; the same Docker image can be deployed to staging and production without modifying runtime environment variables in the browser.

## 6. How did you ensure idempotency in your deployment pipeline?
Idempotency is ensured by deploying immutable artifacts and declarative Kubernetes manifests. Every container image is tagged with a unique Git commit SHA (`k8s/overlays/prod/kustomization.yaml` is dynamically updated). Applying the manifest via `kubectl apply` is declarative; if the cluster state already matches the desired state, no changes are made.

## 7. Explain your approach to handling rate limits from the external LLM providers.
Since we use free tiers of Groq and Gemini, we can easily hit rate limits. To handle this, I implemented an asynchronous fallback chain in the backend Triage Engine. If the primary provider (e.g., Groq) returns a 429 Too Many Requests, the application catches the specific exception and automatically re-routes the request to the secondary provider (e.g., Gemini). We also cache identical complaint descriptions in Redis for 1 hour to prevent redundant LLM calls.

## 8. If this system were to scale to 100x the traffic, what architectural changes would you make?
For 100x traffic:
1. **Message Queue:** I would decouple the triage process from the synchronous HTTP request path by introducing a message broker like RabbitMQ or Kafka. Complaints would be ingested immediately, and background workers would process the LLM triage asynchronously.
2. **Database Sharding/Read Replicas:** The single Postgres instance would become a bottleneck. We would need read replicas for the `GET` endpoints and potentially partition the `complaints` table by region or time.
3. **Dedicated Local LLM:** Relying on external APIs for triage would become too expensive and unreliable. I would deploy a local tuned model (like Llama 3 8B) on GPU nodes within the cluster for first-pass triage.
