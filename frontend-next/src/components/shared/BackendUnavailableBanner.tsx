import { WifiOff } from "lucide-react";

import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";

export function BackendUnavailableBanner() {
  return (
    <Alert className="border-amber-200 bg-amber-50 text-amber-900">
      <WifiOff className="size-4" />
      <AlertTitle>Backend unavailable</AlertTitle>
      <AlertDescription>
        The FastAPI backend is unreachable on the configured API base URL.
      </AlertDescription>
    </Alert>
  );
}
