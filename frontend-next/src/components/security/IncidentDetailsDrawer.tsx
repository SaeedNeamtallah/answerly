"use client";

import { useState } from "react";
import { useQuery, useMutation } from "@tanstack/react-query";
import { format } from "date-fns";
import { toast } from "sonner";
import {
  Activity,
  AlertTriangle,
  Ban,
  CheckCircle2,
  Clock,
  LockOpen,
  ShieldAlert,
  ShieldBan,
  UserX,
  X
} from "lucide-react";

import {
  Drawer,
  DrawerContent,
  DrawerHeader,
  DrawerTitle,
  DrawerDescription,
  DrawerFooter,
  DrawerClose,
} from "@/components/ui/drawer";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import { incidentsApi } from "@/lib/api/incidents";
import { Skeleton } from "@/components/ui/skeleton";

export function IncidentDetailsDrawer({
  incidentId,
  onClose,
  onUpdated
}: {
  incidentId: number;
  onClose: () => void;
  onUpdated: () => void;
}) {
  const [notes, setNotes] = useState("");

  const { data: details, isLoading, refetch } = useQuery({
    queryKey: ["incident-details", incidentId],
    queryFn: () => incidentsApi.getIncidentDetails(incidentId),
  });

  const actionMutation = useMutation({
    mutationFn: ({ type, meta }: { type: string, meta?: any }) => {
      switch (type) {
        case "assign": return incidentsApi.assignIncident(incidentId);
        case "updateNotes": return incidentsApi.updateNotes(incidentId, meta);
        case "status": return incidentsApi.updateStatus(incidentId, meta);
        case "falsePositive": return incidentsApi.markFalsePositive(incidentId, meta);
        case "reopen": return incidentsApi.reopenIncident(incidentId);
        case "suspend": return incidentsApi.takeAction(incidentId, "suspend_user", { reason: "Suspicious activity detected", duration_minutes: 60 });
        case "block": return incidentsApi.takeAction(incidentId, "block_user", { reason: "Confirmed malicious behavior" });
        default: throw new Error("Unknown action");
      }
    },
    onSuccess: () => {
      toast.success("Action applied successfully.");
      refetch();
      onUpdated();
      setNotes("");
    },
    onError: (err: any) => toast.error(err.message || "Failed to apply action."),
  });

  return (
    <Drawer open={!!incidentId} onOpenChange={(open) => !open && onClose()}>
      <DrawerContent className="max-w-4xl mx-auto h-[85vh] mt-24">
        <DrawerHeader className="border-b">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <DrawerTitle className="text-xl">Incident #{incidentId}</DrawerTitle>
              {details && (
                <Badge variant={details.status === "CLOSED" || details.status === "RESOLVED" ? "secondary" : "default"}>
                  {details.status}
                </Badge>
              )}
            </div>
            <DrawerClose asChild>
              <Button variant="ghost" size="icon"><X className="size-4" /></Button>
            </DrawerClose>
          </div>
          <DrawerDescription>
            {details?.incident_type} &middot; Severity: {details?.severity}
          </DrawerDescription>
        </DrawerHeader>

        <div className="p-4 md:p-6 overflow-y-auto flex-1">
          {isLoading || !details ? (
            <div className="space-y-4">
              <Skeleton className="h-24 w-full" />
              <Skeleton className="h-64 w-full" />
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

              <div className="md:col-span-2 space-y-6">
                <div>
                  <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">Investigation Notes</h3>
                  {details.investigation_notes ? (
                    <div className="bg-slate-50 dark:bg-slate-900 rounded-md p-4 text-sm text-slate-700 dark:text-slate-300 border">
                      {details.investigation_notes}
                    </div>
                  ) : (
                    <p className="text-sm text-slate-400 italic">No notes added yet.</p>
                  )}

                  <div className="mt-4 flex gap-2">
                    <Textarea
                      placeholder="Add new investigation notes..."
                      className="min-h-[80px]"
                      value={notes}
                      onChange={(e) => setNotes(e.target.value)}
                    />
                  </div>
                  <div className="mt-2 flex justify-end">
                    <Button
                      size="sm"
                      onClick={() => actionMutation.mutate({ type: "updateNotes", meta: (details.investigation_notes ? details.investigation_notes + "\n\n" : "") + notes })}
                      disabled={!notes.trim() || actionMutation.isPending}
                    >
                      Append Note
                    </Button>
                  </div>
                </div>

                <div>
                  <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-3">Related Events</h3>
                  <div className="border rounded-md divide-y">
                    {details.events?.length === 0 && (
                      <div className="p-4 text-sm text-center text-slate-500">No events linked to this incident.</div>
                    )}
                    {details.events?.map(ev => (
                      <div key={ev.id} className="p-3 text-sm flex justify-between items-start">
                        <div>
                          <div className="font-medium">{ev.event_type}</div>
                          <div className="text-slate-500 mt-1">{ev.message}</div>
                        </div>
                        <span className="text-xs text-slate-400">
                          {format(new Date(ev.timestamp), "MMM d, HH:mm:ss")}
                        </span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Sidebar actions */}
              <div className="space-y-6">
                <div className="rounded-md border p-4 bg-slate-50/50 dark:bg-slate-900/50 space-y-3">
                  <h3 className="font-semibold">Details</h3>
                  <div className="text-sm flex justify-between">
                    <span className="text-slate-500">Created</span>
                    <span className="font-medium">{format(new Date(details.created_at), "MMM d, HH:mm")}</span>
                  </div>
                  <div className="text-sm flex justify-between">
                    <span className="text-slate-500">Actor ID</span>
                    <span className="font-medium">{details.actor_user_id || "None"}</span>
                  </div>
                  <div className="text-sm flex justify-between">
                    <span className="text-slate-500">Actor IP</span>
                    <span className="font-medium">{details.actor_ip || "Unknown"}</span>
                  </div>
                  <div className="text-sm flex justify-between">
                    <span className="text-slate-500">Assigned To</span>
                    <span className="font-medium">{details.assigned_to_username || "Unassigned"}</span>
                  </div>
                </div>

                <div className="space-y-2">
                  <h3 className="text-sm font-semibold text-slate-500 uppercase tracking-wider mb-2">Lifecycle</h3>

                  {!details.assigned_to_id && details.status === "OPEN" && (
                    <Button variant="outline" className="w-full justify-start" onClick={() => actionMutation.mutate({ type: "assign" })}>
                      Assign to me
                    </Button>
                  )}

                  {details.status === "OPEN" && (
                    <Button variant="outline" className="w-full justify-start" onClick={() => actionMutation.mutate({ type: "status", meta: "INVESTIGATING" })}>
                      <Activity className="size-4 mr-2 text-blue-500" />
                      Mark Investigating
                    </Button>
                  )}

                  {(details.status === "OPEN" || details.status === "INVESTIGATING") && (
                    <Button variant="outline" className="w-full justify-start" onClick={() => actionMutation.mutate({ type: "status", meta: "RESOLVED" })}>
                      <CheckCircle2 className="size-4 mr-2 text-emerald-500" />
                      Resolve Incident
                    </Button>
                  )}

                  {details.status === "RESOLVED" && (
                    <Button variant="outline" className="w-full justify-start" onClick={() => actionMutation.mutate({ type: "status", meta: "CLOSED" })}>
                      <Ban className="size-4 mr-2 text-slate-500" />
                      Close Incident
                    </Button>
                  )}

                  {(details.status === "CLOSED" || details.status === "RESOLVED") && (
                    <Button variant="outline" className="w-full justify-start" onClick={() => actionMutation.mutate({ type: "reopen" })}>
                      <LockOpen className="size-4 mr-2" />
                      Reopen Incident
                    </Button>
                  )}

                  {!details.is_false_positive && (details.status !== "CLOSED") && (
                    <Button variant="outline" className="w-full justify-start" onClick={() => actionMutation.mutate({ type: "falsePositive", meta: true })}>
                      <ShieldAlert className="size-4 mr-2 text-amber-500" />
                      Mark False Positive
                    </Button>
                  )}
                </div>

                {details.actor_user_id && (details.status !== "CLOSED") && (
                  <div className="space-y-2 pt-4 border-t">
                    <h3 className="text-sm font-semibold text-rose-600 uppercase tracking-wider mb-2">Threat Actions</h3>

                    <Button variant="destructive" className="w-full justify-start" onClick={() => actionMutation.mutate({ type: "suspend" })}>
                      <Clock className="size-4 mr-2" />
                      Suspend Actor (1h)
                    </Button>
                    <Button variant="destructive" className="w-full justify-start" onClick={() => actionMutation.mutate({ type: "block" })}>
                      <UserX className="size-4 mr-2" />
                      Block Actor Permanently
                    </Button>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </DrawerContent>
    </Drawer>
  );
}
