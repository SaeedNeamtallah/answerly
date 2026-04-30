import { type ReactNode } from "react";

import { DocumentAsset } from "@/lib/types/document";
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
      columns={["File", "Size", "Status", "Actions"]}
      rows={documents.map((document) => [
        document.original_filename,
        formatBytes(document.file_size),
        <StatusBadge key={document.id} status={document.status} />,
        renderActions(document),
      ])}
    />
  );
}
