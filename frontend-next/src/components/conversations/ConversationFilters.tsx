"use client";

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

export function ConversationFilters({
  status,
  onStatusChange,
}: {
  status: string;
  onStatusChange: (value: string) => void;
}) {
  return (
    <div className="flex gap-3">
      <Select value={status} onValueChange={onStatusChange}>
        <SelectTrigger className="w-56 bg-white">
          <SelectValue placeholder="Filter by status" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">All</SelectItem>
          <SelectItem value="open">Open</SelectItem>
          <SelectItem value="escalated">Escalated</SelectItem>
          <SelectItem value="resolved">Resolved</SelectItem>
          <SelectItem value="blocked">Blocked</SelectItem>
        </SelectContent>
      </Select>
    </div>
  );
}
