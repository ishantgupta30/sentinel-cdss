import hashlib, logging, asyncio
from typing import Any, Type
from google import genai
from google.genai import types
from pydantic import BaseModel
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential
from app.config import settings

logger = logging.getLogger("CDSS.Gemini")
MODEL_ID = "gemini-2.5-flash"

class AsyncGeminiClient:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    @retry(stop=stop_after_attempt(6), wait=wait_exponential(multiplier=2, min=15, max=90),
           retry=retry_if_exception_type(Exception), reraise=True)
    async def generate_structured(self, system_instruction: str, prompt: str, schema: Type[BaseModel]) -> Any:
        logger.info(f"Gemini | model={MODEL_ID} | schema={schema.__name__}")
        await asyncio.sleep(13)  # stay under 5 req/min limit
        response = await self.client.aio.models.generate_content(
            model=MODEL_ID,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.0,
                response_mime_type="application/json",
                response_schema=schema,
            ),
        )
        return schema.model_validate_json(response.text)

async_gemini = AsyncGeminiClient()
