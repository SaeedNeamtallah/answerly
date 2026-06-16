import { type ReactNode } from "react";

export function FormSection({
  title,
  description,
  children,
  footer,
}: {
  title: string;
  description?: string;
  children: ReactNode;
  footer?: ReactNode;
}) {
  return (
    <section className="rounded-xl border border-border bg-card shadow-sm">
      <div className="flex flex-col gap-1 border-b border-border px-4 py-4">
        <h2 className="text-base font-semibold text-foreground">{title}</h2>
        {description ? <p className="text-sm text-muted-foreground">{description}</p> : null}
      </div>
      <div className="px-4 py-4">{children}</div>
      {footer ? <div className="border-t border-border bg-muted/40 px-4 py-3">{footer}</div> : null}
    </section>
  );
}
