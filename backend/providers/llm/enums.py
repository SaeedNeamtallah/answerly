"""
Enumerations for supported LLM and embedding providers.
"""
from enum import Enum


class LLMProvider(str, Enum):
    GEMINI = "gemini"
    GEMINI_2_5_LITE_FLASH = "gemini-2.5-lite-flash"
    OPENROUTER_GEMINI_2_0_FLASH = "openrouter-gemini-2.0-flash"
    OPENROUTER_FREE = "openrouter-free"
    OPENROUTER_GEMMA_4_26B_A4B = "openrouter-gemma-4-26b-a4b"
    GROQ_LLAMA_3_3_70B_VERSATILE = "groq-llama-3.3-70b-versatile"
    CEREBRAS_LLAMA_3_1_8B = "cerebras-llama-3.1-8b"


class EmbeddingProvider(str, Enum):
    GEMINI = "gemini"
    COHERE = "cohere"
