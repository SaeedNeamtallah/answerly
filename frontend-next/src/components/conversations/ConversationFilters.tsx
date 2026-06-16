"use client";

import { ListFilter } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const statuses = ["all", "open", "escalated", "resolved", "blocked"];

export function ConversationFilters({
  status,
  onStatusChange,
}: {
  status: string;
  onStatusChange: (value: string) => void;
}) {
  return (
    <div className="flex flex-col gap-3 rounded-xl border bg-card p-3 shadow-sm md:flex-row md:items-center md:justify-between">
      <div className="flex items-center gap-2 text-sm font-medium text-muted-foreground">
        <ListFilter className="size-4" />
        Status filter
      </div>
      <div className="hidden flex-wrap gap-2 md:flex">
        {statuses.map((item) => (
          <Button
            key={item}
            type="button"
            size="sm"
            variant={status === item ? "default" : "outline"}
            onClick={() => onStatusChange(item)}
            className="capitalize"
          >
            {item}
          </Button>
        ))}
      </div>
      <Select value={status} onValueChange={onStatusChange}>
        <SelectTrigger className="w-full bg-background md:hidden">
          <SelectValue placeholder="Filter by status" />
        </SelectTrigger>
        <SelectContent>
          {statuses.map((item) => (
            <SelectItem key={item} value={item} className="capitalize">
              {item}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}
