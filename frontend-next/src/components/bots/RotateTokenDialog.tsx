"use client";

import { useState } from "react";
import { Loader2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";

export function RotateTokenDialog({
  onSubmit,
  isPending,
}: {
  onSubmit: (token: string) => void;
  isPending: boolean;
}) {
  const [token, setToken] = useState("");

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline">Rotate token</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Rotate Telegram token</DialogTitle>
        </DialogHeader>
        <div className="space-y-4">
          <Input
            value={token}
            onChange={(event) => setToken(event.target.value)}
            placeholder="Paste new BotFather token"
            type="password"
          />
          <Button onClick={() => onSubmit(token)} disabled={isPending || !token.trim()}>
            {isPending ? <Loader2 className="size-4 animate-spin" /> : null}
            Save new token
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
