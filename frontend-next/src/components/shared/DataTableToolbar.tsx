"use client";

import { type ReactNode } from "react";
import { Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export function DataTableToolbar({
  search,
  searchPlaceholder = "Search...",
  onSearchChange,
  resultLabel,
  action,
}: {
  search?: string;
  searchPlaceholder?: string;
  onSearchChange?: (value: string) => void;
  resultLabel?: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-3 border-b border-border bg-card px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex min-w-0 flex-1 items-center gap-2">
        {onSearchChange ? (
          <div className="relative w-full max-w-md">
            <Search className="pointer-events-none absolute left-2.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={search || ""}
              onChange={(event) => onSearchChange(event.target.value)}
              placeholder={searchPlaceholder}
              className="pl-8"
            />
          </div>
        ) : null}
        {resultLabel ? <span className="shrink-0 text-xs text-muted-foreground">{resultLabel}</span> : null}
      </div>
      {action ? <div className="flex shrink-0 items-center gap-2">{action}</div> : null}
      {!action && onSearchChange ? (
        <Button variant="outline" size="sm" onClick={() => onSearchChange("")} disabled={!search}>
          Clear
        </Button>
      ) : null}
    </div>
  );
}
