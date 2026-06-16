import { type ReactNode } from "react";

import { DocumentAsset } from "@/lib/types/document";
import { formatRelativeDate } from "@/lib/utils/dates";
import { formatBytes } from "@/lib/utils/formatters";

import { DataTable } from "@/components/shared/DataTable";
import { StatusBadge } from "@/components/shared/StatusBadge";

export function DocumentsTable({
  documents,
  renderActions,
}: {
  documents: DocumentAsset[];
  renderActions: (document: DocumentAsset) => ReactNode;
}) {
  return (
    <DataTable
      caption="Uploaded documents"
      columns={["File", "Type", "Size", "Uploaded", "Status", "Actions"]}
      rows={documents.map((document) => [
        document.original_filename,
        document.file_type || "unknown",
        formatBytes(document.file_size),
        formatRelativeDate(document.created_at),
        <StatusBadge key={document.id} status={document.status} />,
        renderActions(document),
      ])}
      empty="No documents uploaded yet."
    />
  );
}
