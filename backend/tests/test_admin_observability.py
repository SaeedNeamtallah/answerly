"""Admin observability integration tests."""

import inspect
import unittest

from fastapi.params import Depends as DependsParam

from backend.routes import admin_observability
from backend.security.auth import require_platform_owner_access
from backend.services.observability_service import DASHBOARD_CATALOG, ObservabilityService


class AdminObservabilityTests(unittest.IsolatedAsyncioTestCase):
    def test_observability_routes_require_platform_owner(self):
        for endpoint in (
            admin_observability.list_observability_dashboards,
            admin_observability.get_observability_summary,
        ):
            signature = inspect.signature(endpoint)
            dependency = signature.parameters["_"].default
            self.assertIsInstance(dependency, DependsParam)
            self.assertIs(dependency.dependency, require_platform_owner_access)

    def test_dashboard_catalog_is_allowlisted(self):
        service = ObservabilityService(
            grafana_public_url="http://monitor.local:3000",
            grafana_embed_enabled=True,
            grafana_dashboard_org_id=1,
        )
        dashboards = service.list_dashboards("24h")

        self.assertEqual({item.uid for item in DASHBOARD_CATALOG}, {item["uid"] for item in dashboards})
        self.assertTrue(all(item["url"].startswith("http://monitor.local:3000/d/") for item in dashboards))
        self.assertTrue(all(item["embed_url"] and "kiosk" in item["embed_url"] for item in dashboards))
        self.assertFalse(any("api" in item["url"].lower() and "key" in item["url"].lower() for item in dashboards))

    async def test_summary_marks_monitoring_unavailable_without_fake_values(self):
        service = ObservabilityService(prometheus_base_url="", grafana_public_url="http://monitor.local:3000")
        summary = await service.build_summary("not-a-range")

        self.assertEqual(summary["range"], "1h")
        self.assertEqual(summary["prometheus"]["status"], "unavailable")
        self.assertTrue(all(metric["value"] is None for metric in summary["metrics"]))
        self.assertTrue(all(target["health"] == "unknown" for target in summary["targets"]))


if __name__ == "__main__":
    unittest.main()
