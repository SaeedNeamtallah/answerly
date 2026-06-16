import Link from "next/link";
import { type ReactNode } from "react";
import { ExternalLink } from "lucide-react";

import { AdminCompany } from "@/lib/types/admin";

import { DataTable } from "@/components/shared/DataTable";
import { StatusBadge } from "@/components/shared/StatusBadge";
import { Button } from "@/components/ui/button";

export function CompaniesTable({
  companies,
  renderActions,
}: {
  companies: AdminCompany[];
  renderActions?: (company: AdminCompany) => ReactNode;
}) {
  return (
    <DataTable
      caption="Platform companies"
      columns={["Company", "Role", "Projects", "Bots", "Conversations", "Status", "Open", "Actions"]}
      rows={companies.map((company) => [
        company.company_name || company.username,
        company.role,
        String(company.project_count || 0),
        String(company.bot_count || 0),
        String(company.conversation_count || 0),
        <StatusBadge key={company.id} status={company.status} />,
        <Button key={`company-${company.id}`} asChild size="sm" variant="outline">
          <Link href={`/admin/companies/${company.id}`}>
            <ExternalLink className="size-3.5" />
            Details
          </Link>
        </Button>,
        renderActions?.(company) || "—",
      ])}
    />
  );
}
