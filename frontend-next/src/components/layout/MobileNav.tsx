"use client";

import { Menu } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { NavItem, Sidebar } from "@/components/layout/Sidebar";

export function MobileNav({ items }: { items: NavItem[] }) {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" size="icon" className="lg:hidden">
          <Menu />
        </Button>
      </SheetTrigger>
      <SheetContent side="left" className="w-80 border-white/10 bg-[#020a18] p-0 text-white">
        <SheetTitle className="sr-only">Navigation</SheetTitle>
        <Sidebar items={items} embedded />
      </SheetContent>
    </Sheet>
  );
}
