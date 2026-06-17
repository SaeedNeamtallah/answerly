"use client";

import dynamic from "next/dynamic";

import { LoadingState } from "@/components/shared/LoadingState";

const StatsContent = dynamic(() => import("./StatsContent"), {
  ssr: false,
  loading: () => <LoadingState label="Loading admin stats..." />,
});

export default function AdminStatsPage() {
  return <StatsContent />;
}
