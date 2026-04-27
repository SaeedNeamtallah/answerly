from typing import List, Optional, AsyncIterator
import google.generativeai as genai
import asyncio
import logging

from backend.config import settings
from backend.providers.llm.interface import LLMInterface

logger = logging.getLogger(__name__)


class GeminiProvider(LLMInterface):

    def __init__(self, api_key: Optional[str] = None):
        # ✅ FIX: define api_key properly
        self.api_key = api_key or settings.google_api_key
        
        if not self.api_key:
            raise ValueError("Missing GOOGLE_API_KEY in .env")

        genai.configure(api_key=self.api_key)

        self.model_name = settings.gemini_model
        self.embed_model = settings.gemini_embed_model

        self.model = genai.GenerativeModel(self.model_name)

        logger.info(f"Gemini initialized: {self.model_name}")

    # ---------------- TEXT ----------------
    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> str:

        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens or 2048
        )

        loop = asyncio.get_event_loop()

        response = await loop.run_in_executor(
            None,
            lambda: self.model.generate_content(
                full_prompt,
                generation_config=config
            )
        )

        return response.text

    # ---------------- STREAM ----------------
    async def generate_text_stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
        **kwargs
    ) -> AsyncIterator[str]:

        full_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

        config = genai.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens or 2048
        )

        loop = asyncio.get_event_loop()

        response = await loop.run_in_executor(
            None,
            lambda: self.model.generate_content(
                full_prompt,
                generation_config=config,
                stream=True
            )
        )

        for chunk in response:
            if chunk.text:
                yield chunk.text

    # ---------------- EMBEDDINGS ----------------
    async def generate_embeddings(self, texts: List[str]) -> List[List[float]]:

        loop = asyncio.get_event_loop()

        def embed(text):
            return genai.embed_content(
                model=self.embed_model,
                content=text,
                task_type="retrieval_document"
            )["embedding"]

        tasks = [loop.run_in_executor(None, embed, t) for t in texts]

        return await asyncio.gather(*tasks)

    def get_model_name(self):
        return self.model_name

    def get_embedding_dimension(self):
        return 768