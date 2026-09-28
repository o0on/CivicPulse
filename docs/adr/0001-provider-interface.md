# ADR 0001: Use Python `Protocol` for TriageProvider Interface

**Date:** 2026-09-26
**Status:** Accepted

## Context
The application needs to interact with multiple LLM providers (Groq, Gemini) and a local dummy provider for fallback. We need a way to define a strict contract for these providers so they can be easily swapped or mocked during testing.

## Decision
We decided to use Python's `typing.Protocol` (structural subtyping / duck typing) to define the `TriageProvider` interface, rather than using `abc.ABC` (Abstract Base Classes) which requires explicit inheritance.

## Rationale
1. **Decoupling:** `Protocol` allows us to write provider implementations that conform to the interface without needing to import and inherit from the base class. This keeps the provider modules strictly isolated.
2. **Testing:** It is easier to create ad-hoc mock objects in tests that implicitly satisfy the `Protocol` without complex subclassing.
3. **Modern Python Idiom:** Structural subtyping aligns well with modern Python type checking (mypy, pyright) and feels more Pythonic than rigid inheritance trees.

## Consequences
- **Positive:** Adding a new provider (e.g., OpenAI) requires no changes to the base interfaces, just a class with a matching `triage_complaint` method signature.
- **Negative:** Developers unfamiliar with `Protocol` might find it confusing that a class implements an interface without explicitly subclassing it.
