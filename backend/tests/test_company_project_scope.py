"""Static tests for existing company project/document/query ownership scope."""

import inspect
import unittest

from fastapi.params import Depends as DependsParam

from backend.routes import documents, projects, query
from backend.security.auth import get_current_db_user


class CompanyProjectScopeTests(unittest.TestCase):
    def test_project_document_query_routes_require_db_user(self):
        for endpoint in (
            projects.list_projects,
            projects.get_project,
            documents.list_project_documents,
            query.query_project,
        ):
            signature = inspect.signature(endpoint)
            dependency = signature.parameters["current_user"].default
            self.assertIsInstance(dependency, DependsParam)
            self.assertIs(dependency.dependency, get_current_db_user)

    def test_query_scope_helper_requires_current_user_parameter(self):
        signature = inspect.signature(query._ensure_query_scope)

        self.assertIn("current_user", signature.parameters)
        self.assertIn("project_id", signature.parameters)
        self.assertIn("asset_id", signature.parameters)


if __name__ == "__main__":
    unittest.main()

