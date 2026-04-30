import Link from "next/link";
import { type ReactNode } from "react";

import { AdminCompany } from "@/lib/types/admin";

import { DataTable } from "@/components/shared/DataTable";
import { StatusBadge } from "@/components/shared/StatusBadge";

export function CompaniesTable({
  companies,
  renderActions,
}: {
  companies: AdminCompany[];
  renderActions?: (company: AdminCompany) => ReactNode;
}) {
  return (
    <DataTable
      columns={["Company", "Role", "Status", "Open", "Actions"]}
      rows={companies.map((company) => [
        company.company_name || company.username,
        company.role,
        <StatusBadge key={company.id} status={company.status} />,
        <Link key={`company-${company.id}`} href={`/admin/companies/${company.id}`} className="text-indigo-600">
          Details
        </Link>,
        renderActions?.(company) || "—",
      ])}
    />
  );
}
