"""
Enumerations for supported LLM and embedding providers.
"""
from enum import Enum


class LLMProvider(str, Enum):
    GEMINI = "gemini"
    GEMINI_2_5_LITE_FLASH = "gemini-2.5-lite-flash"
    OPENROUTER_GEMINI_2_0_FLASH = "openrouter-gemini-2.0-flash"
    OPENROUTER_FREE = "openrouter-free"
    GROQ_LLAMA_3_3_70B_VERSATILE = "groq-llama-3.3-70b-versatile"
    GROQ_GPT_OSS_120B = "groq-gpt-oss-120b"
    CEREBRAS_LLAMA_3_3_70B = "cerebras-llama-3.3-70b"
    CEREBRAS_LLAMA_3_1_8B = "cerebras-llama-3.1-8b"
    CEREBRAS_GPT_OSS_120B = "cerebras-gpt-oss-120b"


class EmbeddingProvider(str, Enum):
    GEMINI = "gemini"
    COHERE = "cohere"
    VOYAGE = "voyage"
    BGE_M3 = "bge-m3"
    HF_BGE_M3 = "hf-bge-m3"
