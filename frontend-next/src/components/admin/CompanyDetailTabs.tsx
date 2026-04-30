import { type ReactNode } from "react";

import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

export function CompanyDetailTabs({
  overview,
  projects,
  bots,
  conversations,
}: {
  overview: ReactNode;
  projects: ReactNode;
  bots: ReactNode;
  conversations: ReactNode;
}) {
  return (
    <Tabs defaultValue="overview" className="space-y-4">
      <TabsList>
        <TabsTrigger value="overview">Overview</TabsTrigger>
        <TabsTrigger value="projects">Projects</TabsTrigger>
        <TabsTrigger value="bots">Bots</TabsTrigger>
        <TabsTrigger value="conversations">Conversations</TabsTrigger>
      </TabsList>
      <TabsContent value="overview">{overview}</TabsContent>
      <TabsContent value="projects">{projects}</TabsContent>
      <TabsContent value="bots">{bots}</TabsContent>
      <TabsContent value="conversations">{conversations}</TabsContent>
    </Tabs>
  );
}
