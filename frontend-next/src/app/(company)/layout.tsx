import { AppShell } from "@/components/layout/AppShell";

export default function CompanyLayout({ children }: { children: React.ReactNode }) {
  return <AppShell variant="company">{children}</AppShell>;
}
