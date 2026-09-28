import json

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.providers.triage.base import TriageResult
from app.providers.triage.llm import TriageError


class OllamaTriage:
    name: str = "llm:ollama"

    def __init__(self, base_url: str, model: str = "llama3.2:3b"):
        self.base_url = base_url
        self.model = model
        self.client = httpx.AsyncClient(timeout=10.0)

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type((httpx.TimeoutException, httpx.ConnectError, httpx.ReadError))
    )
    async def triage(self, text: str, location: str) -> TriageResult:
        prompt = f"""You are a municipal complaint classifier. Classify the complaint below.

<complaint_body>
{text}
</complaint_body>

Location: {location}

Respond ONLY with valid JSON:
{{"category": "water|electricity|sanitation|roads|streetlights|other",
  "priority": "high|normal|low",
  "summary": "<max 140 chars>",
  "confidence": 0.0-1.0}}"""

        url = f"{self.base_url.rstrip('/')}/api/chat"
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "format": "json",
            "stream": False
        }

        response = await self.client.post(url, json=payload)
        
        if response.status_code == 429 or response.status_code >= 500:
            response.raise_for_status()
        elif response.status_code >= 400:
            raise TriageError(f"Client error: {response.text}")
            
        try:
            data = response.json()
            content = data["message"]["content"]
            parsed = json.loads(content)
            return TriageResult(**parsed)
        except (KeyError, json.JSONDecodeError, ValueError) as e:
            raise TriageError(f"Failed to parse Ollama response: {e}")
