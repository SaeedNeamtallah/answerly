import { type ReactNode } from "react";

export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
}: {
  eyebrow?: string;
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="flex flex-col gap-4 md:flex-row md:items-end md:justify-between">
      <div className="space-y-2">
        {eyebrow ? <p className="text-sm font-medium uppercase tracking-[0.2em] text-indigo-600">{eyebrow}</p> : null}
        <h1 className="text-3xl font-semibold tracking-tight text-slate-950">{title}</h1>
        {description ? <p className="max-w-3xl text-sm text-slate-600">{description}</p> : null}
      </div>
      {actions ? <div className="flex items-center gap-3">{actions}</div> : null}
    </div>
  );
}
