"use client";

import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { format } from "date-fns";
import { Download, RefreshCw, Wifi } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { securityApi } from "@/lib/api/security";
import { getApiUrl } from "@/lib/api/client";
import type { SecurityEvent } from "@/lib/types/security";
import { readAccessToken } from "@/store/auth-store";
import { Skeleton } from "@/components/ui/skeleton";

function getSeverityColor(severity: string) {
  switch (severity.toUpperCase()) {
    case "CRITICAL":
      return "bg-rose-100 dark:bg-rose-500/20 text-rose-700 dark:text-rose-400 hover:bg-rose-200 dark:hover:bg-rose-500/30 border-rose-200 dark:border-rose-500/50";
    case "HIGH":
      return "bg-orange-100 dark:bg-orange-500/20 text-orange-700 dark:text-orange-400 hover:bg-orange-200 dark:hover:bg-orange-500/30 border-orange-200 dark:border-orange-500/50";
    case "MEDIUM":
      return "bg-amber-100 dark:bg-amber-500/20 text-amber-700 dark:text-amber-400 hover:bg-amber-200 dark:hover:bg-amber-500/30 border-amber-200 dark:border-amber-500/50";
    default:
      return "bg-slate-100 dark:bg-slate-500/20 text-slate-700 dark:text-slate-400 hover:bg-slate-200 dark:hover:bg-slate-500/30 border-slate-200 dark:border-slate-500/50";
  }
}

export function EventsFeed() {
  const [liveEvents, setLiveEvents] = useState<SecurityEvent[]>([]);
  const [isLive, setIsLive] = useState(false);

  const { data: initialEvents, isLoading, refetch } = useQuery({
    queryKey: ["security-events", "feed"],
    queryFn: () => securityApi.getEvents(30),
    staleTime: 0,
  });

  // Combine live and initial
  const displayEvents = [
    ...liveEvents,
    ...(initialEvents || [])
  ].slice(0, 50);

  useEffect(() => {
    const abortController = new AbortController();

    async function connectSSE() {
      const token = readAccessToken();
      if (!token) return;

      try {
        setIsLive(false);
        const res = await fetch(getApiUrl("/security/events/stream"), {
          headers: {
            Authorization: `Bearer ${token}`,
          },
          signal: abortController.signal,
        });

        if (res.status === 401 || res.status === 403) {
          setIsLive(false);
          return;
        }

        if (!res.ok || !res.body) throw new Error("Failed to connect");

        setIsLive(true);
        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const lines = buffer.split("\n\n");
          buffer = lines.pop() || "";

          for (const block of lines) {
            const dataLine = block.split("\n").find(line => line.startsWith("data: "));
            if (dataLine) {
              try {
                const dataStr = dataLine.replace("data: ", "").trim();
                if (dataStr === "keepalive") continue;

                const event = JSON.parse(dataStr) as { type?: string; data?: SecurityEvent };
                if (event.type === "event" && event.data) {
                  setLiveEvents(prev => [event.data as SecurityEvent, ...prev].slice(0, 50));
                }
              } catch (e) {
                console.error("SSE parse error", e);
              }
            }
          }
        }
      } catch (err) {
        if ((err as Error).name !== "AbortError") {
          console.error("SSE disconnected", err);
          setIsLive(false);
          // Retry after 5 seconds
          setTimeout(() => {
            if (!abortController.signal.aborted) connectSSE();
          }, 5000);
        }
      }
    }

    connectSSE();

    return () => {
      abortController.abort();
    };
  }, []);

  const handleExport = () => {
    const token = readAccessToken();

    fetch(getApiUrl("/security/events/export"), {
      headers: { Authorization: `Bearer ${token}` }
    })
      .then(res => res.blob())
      .then(blob => {
        const a = document.createElement('a');
        a.href = window.URL.createObjectURL(blob);
        a.download = `security-events-${format(new Date(), 'yyyyMMdd_HHmmss')}.csv`;
        document.body.appendChild(a);
        a.click();
        a.remove();
      });
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <h2 className="text-lg font-semibold tracking-tight">Security Events Feed</h2>
          {isLive ? (
            <Badge variant="outline" className="bg-emerald-500/10 text-emerald-500 border-emerald-500/20 gap-1.5 font-medium animate-in fade-in">
              <span className="relative flex size-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full size-2 bg-emerald-500"></span>
              </span>
              Live
            </Badge>
          ) : (
            <Badge variant="outline" className="bg-slate-500/10 text-slate-500 border-slate-500/20 gap-1.5 font-medium">
              <Wifi className="size-3" />
              Reconnecting...
            </Badge>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={() => refetch()} className="h-8">
            <RefreshCw className="mr-2 size-3.5" />
            Refresh
          </Button>
          <Button variant="outline" size="sm" onClick={handleExport} className="h-8">
            <Download className="mr-2 size-3.5" />
            Export CSV
          </Button>
        </div>
      </div>

      <div className="rounded-md border shadow-sm bg-card overflow-hidden">
        <Table>
          <TableHeader>
            <TableRow className="bg-muted/50">
              <TableHead className="w-[180px]">Timestamp</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Severity</TableHead>
              <TableHead>Actor</TableHead>
              <TableHead>Message</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {isLoading ? (
              Array.from({ length: 5 }).map((_, i) => (
                <TableRow key={i}>
                  <TableCell><Skeleton className="h-5 w-32" /></TableCell>
                  <TableCell><Skeleton className="h-5 w-24" /></TableCell>
                  <TableCell><Skeleton className="h-5 w-20" /></TableCell>
                  <TableCell><Skeleton className="h-5 w-24" /></TableCell>
                  <TableCell><Skeleton className="h-5 w-full max-w-md" /></TableCell>
                </TableRow>
              ))
            ) : displayEvents.length === 0 ? (
              <TableRow>
                <TableCell colSpan={5} className="h-24 text-center text-muted-foreground">
                  No security events found.
                </TableCell>
              </TableRow>
            ) : (
              displayEvents.map((event, idx) => {
                // Determine if this is a newly arrived live event
                const isNew = liveEvents.some(e => e.id === event.id);
                return (
                  <TableRow
                    key={event.id}
                    className={isNew ? "bg-indigo-50/50 dark:bg-indigo-900/10 transition-colors duration-1000" : ""}
                  >
                    <TableCell className="text-sm font-medium whitespace-nowrap text-muted-foreground">
                      {format(new Date(event.timestamp), "MMM d, HH:mm:ss")}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className="font-mono text-[10px] uppercase">
                        {event.event_type}
                      </Badge>
                      {event.is_simulation && (
                        <Badge variant="secondary" className="ml-2 text-[10px]">SIM</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline" className={getSeverityColor(event.severity)}>
                        {event.severity}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-muted-foreground">
                      {event.username || event.ip_address || "System"}
                    </TableCell>
                    <TableCell className="text-sm text-slate-700 dark:text-slate-300">
                      {event.message}
                    </TableCell>
                  </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </div>
    </div>
  );
}
