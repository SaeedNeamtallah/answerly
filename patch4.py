with open('backend/controllers/query_controller.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace(
    '        language: str = "ar",\n        asset_id: Optional[int] = None\n    ) -> Dict[str, Any]:',
    '        language: str = "ar",\n        asset_id: Optional[int] = None,\n        custom_system_prompt: Optional[str] = None\n    ) -> Dict[str, Any]:'
)

text = text.replace(
    '            result = await self.answer_service.generate_answer(\n                query=query,\n                context_chunks=similar_chunks,\n                language=language,\n                include_sources=True\n            )',
    '            result = await self.answer_service.generate_answer(\n                query=query,\n                context_chunks=similar_chunks,\n                language=language,\n                include_sources=True,\n                custom_system_prompt=custom_system_prompt\n            )'
)

with open('backend/controllers/query_controller.py', 'w', encoding='utf-8') as f:
    f.write(text)
