"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";

import { Button } from "@/components/ui/button";

export function DataTablePagination({
  pageIndex,
  pageCount,
  canPreviousPage,
  canNextPage,
  onPreviousPage,
  onNextPage,
  itemLabel,
}: {
  pageIndex: number;
  pageCount: number;
  canPreviousPage: boolean;
  canNextPage: boolean;
  onPreviousPage: () => void;
  onNextPage: () => void;
  itemLabel?: string;
}) {
  return (
    <div className="flex flex-col gap-3 border-t border-border bg-card px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
      <p className="text-xs text-muted-foreground">{itemLabel || "Showing current page"}</p>
      <div className="flex items-center gap-2">
        <Button variant="outline" size="icon-sm" onClick={onPreviousPage} disabled={!canPreviousPage} aria-label="Previous page">
          <ChevronLeft />
        </Button>
        <span className="min-w-16 text-center text-sm font-medium">
          {pageIndex + 1} / {Math.max(pageCount, 1)}
        </span>
        <Button variant="outline" size="icon-sm" onClick={onNextPage} disabled={!canNextPage} aria-label="Next page">
          <ChevronRight />
        </Button>
      </div>
    </div>
  );
}
