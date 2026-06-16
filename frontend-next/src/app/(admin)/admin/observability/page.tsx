import { AdminObservabilityPanel } from "@/components/admin/AdminObservabilityPanel";
import { PageHeader } from "@/components/layout/PageHeader";

export default function AdminObservabilityPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Platform telemetry"
        title="Observability"
        description="Platform-owner Grafana and Prometheus dashboards for system performance."
      />
      <AdminObservabilityPanel />
    </div>
  );
}
