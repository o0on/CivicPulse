# AI Usage and Attribution

In accordance with academic integrity guidelines, this document outlines the usage of Artificial Intelligence tools during the development of CivicPulse.

## Tools Used
- **GitHub Copilot / Cursor:** Used extensively in the IDE for boilerplate code generation, autocompletion, and writing repetitive Kubernetes manifests (e.g., generating the matching Service for a Deployment).
- **ChatGPT (GPT-4o):** Used for architectural brainstorming, debugging complex Kustomize configurations, and drafting the initial structure for the load testing script.

## Specific Areas of Assistance
1. **Kubernetes Manifests:** I used Copilot to generate the initial YAML for the HPA and VPA, which I then manually tuned to ensure the CPU thresholds matched the assignment requirements.
2. **FastAPI Structure:** ChatGPT suggested the directory structure for the FastAPI backend (separating routers, services, and models) to maintain clean architecture.
3. **Regex Patterns:** The regex patterns used in `scripts/check_submission.py` to identify hardcoded secrets were generated with the help of ChatGPT.

## Reflection
AI tools significantly accelerated the development process, particularly for scaffolding and configuration files. However, I remained the primary architect. I had to manually debug the GitHub Actions CD pipeline when the SHA image tag replacement failed, as the AI suggestions did not perfectly align with the specific directory structure of this repository. All conceptual decisions and the final integration were done independently.
