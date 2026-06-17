"use client";

import { ListFilter, LayoutGrid, List } from "lucide-react";

import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "@/lib/utils/cn";

const statuses = ["all", "open", "escalated", "resolved", "blocked"];

export function ConversationFilters({
  status,
  onStatusChange,
}: {
  status: string;
  onStatusChange: (value: string) => void;
}) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
      <div className="flex items-center gap-2">
        <div className="flex items-center rounded-lg border border-slate-200 bg-white p-1 shadow-sm">
          {statuses.map((item) => (
            <button
              key={item}
              type="button"
              onClick={() => onStatusChange(item)}
              className={cn(
                "px-3 py-1.5 text-sm font-medium rounded-md transition-all capitalize",
                status === item
                  ? "bg-slate-100 text-slate-900 shadow-sm"
                  : "text-slate-500 hover:text-slate-900"
              )}
            >
              {item}
            </button>
          ))}
        </div>
      </div>
      
      <div className="flex items-center gap-3">
        <div className="flex items-center rounded-lg border border-slate-200 bg-white p-1 shadow-sm">
          <button className="flex items-center gap-2 rounded-md bg-slate-100 px-3 py-1.5 text-sm font-medium text-slate-900 shadow-sm">
            <List className="size-4" />
            <span className="hidden sm:inline">List view</span>
          </button>
          <button className="flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium text-slate-500 hover:text-slate-900 transition-colors">
            <LayoutGrid className="size-4" />
            <span className="hidden sm:inline">Board view</span>
          </button>
        </div>
        <button className="flex items-center gap-2 rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-slate-600 shadow-sm hover:bg-slate-50 transition-colors">
          <ListFilter className="size-4" />
          More filters
        </button>
      </div>

      <div className="sm:hidden">
        <Select value={status} onValueChange={onStatusChange}>
          <SelectTrigger className="w-full h-10 rounded-xl bg-white border-slate-200">
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
    </div>
  );
}
