import hashlib

from app.models import Category, Priority
from app.providers.triage.base import TriageResult


class SimulatedTriage:
    name: str = "simulated"

    def __init__(self, inject_error: bool = False, error_after_attempts: int = 0):
        self.inject_error = inject_error
        self.error_after_attempts = error_after_attempts
        self.attempts = 0

    async def triage(self, text: str, location: str = "") -> TriageResult:
        self.attempts += 1
        
        if self.inject_error:
            if self.error_after_attempts == 0 or self.attempts > self.error_after_attempts:
                raise RuntimeError("Simulated triage failure")
                
        hash_val = int(hashlib.sha256(text[:10].encode('utf-8')).hexdigest(), 16)
        categories = list(Category)
        category = categories[hash_val % len(categories)]
        
        text_lower = text.lower()
        if "urgent" in text_lower or "emergency" in text_lower:
            priority = Priority.high
        else:
            priority = Priority.normal
            
        return TriageResult(
            category=category,
            priority=priority,
            summary=text.strip()[:100],
            confidence=0.95
        )
