import json
import time
import hashlib
from redis.asyncio import Redis
from app.providers.triage.base import TriageProvider, TriageResult
from app.providers.triage.rules import RuleBasedTriage
import asyncio

class TriageService:
    def __init__(self, provider: TriageProvider, redis: Redis, rules_fallback: RuleBasedTriage):
        self.provider = provider
        self.redis = redis
        self.rules_fallback = rules_fallback
    
    async def triage_complaint(self, text: str, location: str) -> tuple[TriageResult, str, int]:
        cache_key = f"triage_hash:{hashlib.sha256(f'{text}{location}'.encode()).hexdigest()}"
        cached = await self.redis.get(cache_key)
        
        if cached:
            data = json.loads(cached)
            return TriageResult(**data["result"]), data["triaged_by"], data["latency_ms"]

        start = time.perf_counter()
        triaged_by = self.provider.name
        try:
            result = await asyncio.wait_for(self.provider.triage(text, location), timeout=10.0)
        except Exception:
            result = await self.rules_fallback.triage(text, location)
            triaged_by = "rules:fallback"
            
        latency_ms = int((time.perf_counter() - start) * 1000)
        
        cache_data = {
            "result": result.model_dump(),
            "triaged_by": triaged_by,
            "latency_ms": latency_ms
        }
        await self.redis.set(cache_key, json.dumps(cache_data), ex=86400)
        
        return result, triaged_by, latency_ms
