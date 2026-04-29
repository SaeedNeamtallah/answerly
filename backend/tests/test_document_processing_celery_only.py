"""Document processing must route through Celery tasks only."""

import inspect
import unittest

from backend.controllers.document_controller import DocumentController
from backend.routes import documents


class DocumentProcessingCeleryOnlyTests(unittest.IsolatedAsyncioTestCase):
    async def test_document_controller_direct_processing_is_disabled(self):
        controller = DocumentController.__new__(DocumentController)
        with self.assertRaisesRegex(RuntimeError, "Celery process_document_task"):
            await controller.process_document(asset_id=1)

    def test_document_process_route_queues_celery_task(self):
        source = inspect.getsource(documents.process_document)
        self.assertIn("process_document_task.delay", source)
        self.assertNotIn("document_controller.process_document", source)


if __name__ == "__main__":
    unittest.main()
