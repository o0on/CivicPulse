# ADR 0004: PII and Data Governance with External LLMs

**Date:** 2026-09-26
**Status:** Accepted

## Context
Citizens submit unstructured text describing municipal issues. This text may inadvertently contain Personally Identifiable Information (PII) such as names, phone numbers, or exact residential addresses. Currently, this raw text is sent to third-party APIs (Groq, Gemini free tiers) for triage.

## Decision
For the scope of this university prototype assignment, we accept the risk of exposing potential PII to these external APIs. We have documented this risk. The `contact_email` field is explicitly stripped and *never* sent to the LLM, but the raw `description` is sent as-is.

## Rationale
1. **Prototype Constraints:** Implementing a robust, local NLP-based PII scrubber (e.g., using Microsoft Presidio) before the LLM call adds significant complexity and latency that exceeds the requirements of this assignment.
2. **Free Tier Limitations:** We are utilizing free tiers for cost reasons. Enterprise agreements with zero-data-retention policies are not feasible for this project.

## Consequences
- **Positive:** Fast development and high-quality triage using state-of-the-art hosted models.
- **Negative:** Non-compliant with GDPR/CCPA for a real-world municipal application.

## Future Production Roadmap
If this were to go to production, we would implement one of the following:
1. **Local Scrubbing:** Pass the text through a local PII anonymizer (replacing names with `[NAME]`) *before* sending to the external API.
2. **Local LLM Exclusively:** Rely entirely on a locally hosted model (e.g., Ollama running Llama 3) inside the Kubernetes cluster so that citizen data never leaves the municipality's network.
