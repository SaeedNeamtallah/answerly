import asyncio

from backend.providers.llm.factory import LLMProviderFactory


async def main() -> None:
    provider = LLMProviderFactory.create_embedding_provider("gemini")
    declared = provider.get_embedding_dimension()
    vecs = await provider.generate_embeddings(["dimension probe"])
    actual = len(vecs[0]) if vecs and vecs[0] else 0
    print("declared_dimension", declared)
    print("actual_dimension", actual)


if __name__ == "__main__":
    asyncio.run(main())
