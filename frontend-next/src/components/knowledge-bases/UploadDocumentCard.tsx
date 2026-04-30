"use client";

import { Loader2, Upload } from "lucide-react";
import { useRef } from "react";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export function UploadDocumentCard({
  isUploading,
  onSelect,
}: {
  isUploading: boolean;
  onSelect: (file: File) => void;
}) {
  const inputRef = useRef<HTMLInputElement | null>(null);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload document</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-slate-600">
          Files are uploaded to the backend and must be processed through Celery tasks only.
        </p>
        <input
          ref={inputRef}
          className="hidden"
          type="file"
          onChange={(event) => {
            const file = event.target.files?.[0];
            if (file) {
              onSelect(file);
            }
          }}
        />
        <Button onClick={() => inputRef.current?.click()} disabled={isUploading}>
          {isUploading ? <Loader2 className="size-4 animate-spin" /> : <Upload className="size-4" />}
          Upload file
        </Button>
      </CardContent>
    </Card>
  );
}
