"use client";

import { Menu } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { NavItem, Sidebar } from "@/components/layout/Sidebar";

export function MobileNav({ items }: { items: NavItem[] }) {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" size="icon" className="lg:hidden">
          <Menu className="size-4" />
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-80 bg-slate-950 p-0 text-slate-100">
        <Sidebar items={items} />
      </SheetContent>
    </Sheet>
  );
}
