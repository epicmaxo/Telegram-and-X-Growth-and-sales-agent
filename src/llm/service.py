from __future__ import annotations

from dataclasses import dataclass

import json
from openai import AzureOpenAI

@dataclass
class LLMResponse:
    analysis: dict[str, object]

class LLMService:
    def __init__(self, api_key: str | None = None, endpoint: str | None = None, deployment_name: str | None = None, api_version: str | None = None) -> None:
        self.api_key = api_key
        self.endpoint = endpoint
        self.deployment_name = deployment_name
        self.api_version = api_version
        
        self.client = None
        if self.api_key and self.endpoint and self.api_version:
            self.client = AzureOpenAI(
                api_key=self.api_key,
                api_version=self.api_version,
                azure_endpoint=self.endpoint
            )

    def generate(self, prompt: str) -> LLMResponse:
        if not self.client or not self.deployment_name:
            # Fallback to mock if not configured
            return LLMResponse(
                analysis={
                    "prompt": prompt,
                    "mode": "mock",
                    "note": "Azure OpenAI client not configured properly.",
                }
            )
            
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are an AI assistant that analyzes text and returns JSON. Always return valid JSON only, with no markdown formatting or extra text."},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" }
            )
            
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from OpenAI")
                
            parsed_content = json.loads(content)
            return LLMResponse(analysis=parsed_content)
            
        except Exception as e:
            return LLMResponse(
                analysis={
                    "error": str(e),
                    "mode": "error"
                }
            )
