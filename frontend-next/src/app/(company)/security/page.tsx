"use client";

import { useState } from "react";
import { Shield, Zap } from "lucide-react";
import { toast } from "sonner";
import { useMutation, useQueryClient } from "@tanstack/react-query";

import { PageHeader } from "@/components/layout/PageHeader";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { OverviewStats } from "@/components/security/OverviewStats";
import { EventsFeed } from "@/components/security/EventsFeed";
import { IncidentsTab } from "@/components/security/IncidentsTab";
import { securityApi } from "@/lib/api/security";

export default function SecurityCenterPage() {
  const queryClient = useQueryClient();
  const [isSimulating, setIsSimulating] = useState(false);

  const simulateMutation = useMutation({
    mutationFn: () => securityApi.simulateAttack(),
    onSuccess: (data: any) => {
      toast.success(`Simulation complete. Generated ${data.generated_count} events.`);
      queryClient.invalidateQueries({ queryKey: ["security-stats"] });
      queryClient.invalidateQueries({ queryKey: ["security-events"] });
      queryClient.invalidateQueries({ queryKey: ["incidents"] });
      setIsSimulating(false);
    },
    onError: (err: any) => {
      toast.error(err.message || "Simulation failed.");
      setIsSimulating(false);
    }
  });

  const handleSimulate = () => {
    setIsSimulating(true);
    simulateMutation.mutate();
  };

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
