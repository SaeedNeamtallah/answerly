import { PageHeader } from "@/components/layout/PageHeader";
import { SetupChecklist } from "@/components/dashboard/SetupChecklist";

export default function OnboardingPage() {
  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Getting started"
        title="Onboarding"
        description="Use this migration workspace to reach the same backend-powered outcomes as the legacy frontend."
      />
      <SetupChecklist />
    </div>
  );
}
