from backend.config import settings
from backend.runtime_config import get_runtime_value
from backend.providers.llm.factory import LLMProviderFactory

runtime_provider = get_runtime_value("llm_provider", settings.llm_provider)

# Force recreation for this key to show current behavior deterministically.
LLMProviderFactory._llm_instances.pop("gemini-2.5-lite-flash", None)
provider = LLMProviderFactory.create_provider("gemini-2.5-lite-flash")

print("runtime_llm_provider", runtime_provider)
print("requested_provider", "gemini-2.5-lite-flash")
print("resolved_model", provider.get_model_name())
