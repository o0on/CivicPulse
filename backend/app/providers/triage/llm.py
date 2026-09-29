import json

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.providers.triage.base import TriageResult


class TriageError(Exception):
    pass

class LLMTriage:
    def __init__(self, provider: str, api_key: str, model: str, base_url: str | None = None):
        self.provider = provider
        self.name = f"llm:{provider}"
        self.api_key = api_key
        self.model = model
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=10.0)

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=10),
        retry=retry_if_exception_type(
            (httpx.TimeoutException, httpx.ConnectError, httpx.ReadError, httpx.HTTPStatusError)
        ),
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

        if self.provider == "gemini":
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent?key={self.api_key}"
            payload = {
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json"}
            }
            response = await self.client.post(url, json=payload)
            if response.status_code == 429 or response.status_code >= 500:
                response.raise_for_status()
            elif response.status_code >= 400:
                raise TriageError(f"Client error: {response.text}")
            try:
                data = response.json()
                raw_text = data["candidates"][0]["content"]["parts"][0]["text"]
                if raw_text.startswith("```"):
                    raw_text = raw_text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
                parsed = json.loads(raw_text)
                return TriageResult(**parsed)
            except (KeyError, json.JSONDecodeError, ValueError) as e:
                raise TriageError(f"Failed to parse LLM response: {e}")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url.rstrip('/')}/chat/completions" if self.base_url else "https://api.openai.com/v1/chat/completions"
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "response_format": {"type": "json_object"}
        }

        response = await self.client.post(url, json=payload, headers=headers)
        
        if response.status_code == 429 or response.status_code >= 500:
            response.raise_for_status()
        elif response.status_code >= 400:
            raise TriageError(f"Client error: {response.text}")
            
        try:
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            return TriageResult(**parsed)
        except (KeyError, json.JSONDecodeError, ValueError) as e:
            raise TriageError(f"Failed to parse LLM response: {e}")
