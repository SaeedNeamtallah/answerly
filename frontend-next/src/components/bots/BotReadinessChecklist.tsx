import { BotReadinessResponse } from "@/lib/types/bot";

import { ReadinessChecklist } from "@/components/shared/ReadinessChecklist";

export function BotReadinessChecklist({ readiness }: { readiness?: BotReadinessResponse | null }) {
  return <ReadinessChecklist title="Bot readiness" checks={readiness?.checks} />;
}
