"use client";

import dynamic from "next/dynamic";

import { BotIntegration } from "@/lib/types/bot";

import { LoadingState } from "@/components/shared/LoadingState";

const BotHealthPanelContent = dynamic(
  () => import("./BotHealthPanelContent").then((mod) => mod.BotHealthPanelContent),
  { ssr: false, loading: () => <LoadingState label="Loading bot health..." /> }
);

export function BotHealthPanel({ bots }: { bots: BotIntegration[] }) {
  return <BotHealthPanelContent bots={bots} />;
}
