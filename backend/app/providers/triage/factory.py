from app.core.config import settings
from app.providers.triage.base import TriageProvider
from app.providers.triage.llm import LLMTriage
from app.providers.triage.ollama import OllamaTriage
from app.providers.triage.rules import RuleBasedTriage
from app.providers.triage.simulated import SimulatedTriage


def create_triage_provider() -> TriageProvider:
    provider = settings.TRIAGE_PROVIDER
    
    if provider == "llm:groq":
        return LLMTriage(
            provider="groq",
            api_key=settings.GROQ_API_KEY,
            model="llama-3.1-8b-instant",
            base_url="https://api.groq.com/openai/v1"
        )
    elif provider == "llm:gemini":
        return LLMTriage(
            provider="gemini",
            api_key=settings.GEMINI_API_KEY,
            model="gemini-1.5-flash",
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
        )
    elif provider == "llm:ollama":
        return OllamaTriage(
            base_url=settings.OLLAMA_BASE_URL
        )
    elif provider == "simulated":
        return SimulatedTriage()
    else:
        return RuleBasedTriage()
