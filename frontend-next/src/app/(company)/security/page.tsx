"use client";

import { Zap } from "lucide-react";
import { toast } from "sonner";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { PageHeader } from "@/components/layout/PageHeader";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { ErrorState } from "@/components/shared/ErrorState";
import { LoadingState } from "@/components/shared/LoadingState";
import { OverviewStats } from "@/components/security/OverviewStats";
import { EventsFeed } from "@/components/security/EventsFeed";
import { IncidentsTab } from "@/components/security/IncidentsTab";
import { securityApi } from "@/lib/api/security";
import { getApiErrorMessage } from "@/lib/api/client";
import { canAccessSecurityCenter } from "@/lib/auth/permissions";
import type { SecuritySimulationResponse } from "@/lib/types/security";
import { useAuthStore } from "@/store/auth-store";

export default function SecurityCenterPage() {
  const queryClient = useQueryClient();
  const currentUser = useAuthStore((state) => state.currentUser);
  const isHydrated = useAuthStore((state) => state.isHydrated);

  const simulateMutation = useMutation({
    mutationFn: () => securityApi.simulateAttack(),
    onSuccess: (data: SecuritySimulationResponse) => {
      toast.success(`Simulation complete. Generated ${data.generated_count} events.`);
      queryClient.invalidateQueries({ queryKey: ["security-stats"] });
      queryClient.invalidateQueries({ queryKey: ["security-events"] });
      queryClient.invalidateQueries({ queryKey: ["incidents"] });
    },
    onError: (error: Error) => {
      toast.error(getApiErrorMessage(error, "Simulation failed."));
    }
  });

  if (!isHydrated) {
    return <LoadingState label="Checking permissions..." />;
  }

  if (!canAccessSecurityCenter(currentUser)) {
    return (
      <ErrorState
        title="Access forbidden"
        description="Your current role does not have access to the security center."
      />
    );
  }

  const handleSimulate = () => {
    simulateMutation.mutate();
  };

  const isSimulating = simulateMutation.isPending;

  return (
    <div className="flex flex-col gap-6 max-w-[1400px] mx-auto w-full">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <PageHeader
          title="Security Center"
          description="Monitor platform security events, investigate incidents, and manage threat responses."
        />

        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            className="border-indigo-200 text-indigo-700 bg-indigo-50 hover:bg-indigo-100 dark:border-indigo-800 dark:bg-indigo-900/30 dark:text-indigo-300 dark:hover:bg-indigo-900/50"
            onClick={handleSimulate}
            disabled={isSimulating}
          >
            <Zap className={`mr-2 size-4 ${isSimulating ? "animate-pulse" : ""}`} />
            {isSimulating ? "Running Simulation..." : "Simulate Attack"}
          </Button>
        </div>
      </div>

      <OverviewStats />

      <Tabs defaultValue="events" className="w-full mt-2">
        <TabsList className="grid w-full grid-cols-2 max-w-sm mb-6">
          <TabsTrigger value="events">Events Feed</TabsTrigger>
          <TabsTrigger value="incidents">Active Incidents</TabsTrigger>
        </TabsList>

        <TabsContent value="events" className="animate-in fade-in-50 duration-500">
          <EventsFeed />
        </TabsContent>

        <TabsContent value="incidents" className="animate-in fade-in-50 duration-500">
          <IncidentsTab />
        </TabsContent>
      </Tabs>
    </div>
  );
}
