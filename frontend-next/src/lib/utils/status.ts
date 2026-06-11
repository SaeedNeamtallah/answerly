export type StatusVariant = "default" | "secondary" | "success" | "warning" | "danger";

export function getStatusVariant(status?: string | null): StatusVariant {
  const normalized = String(status || "").toLowerCase();

  if (["success", "completed", "ready", "active", "enabled", "resolved"].includes(normalized)) {
    return "success";
  }

  if (["warning", "queued", "pending", "escalated", "processing"].includes(normalized)) {
    return "warning";
  }

  if (["failure", "failed", "error", "blocked", "suspended", "disabled"].includes(normalized)) {
    return "danger";
  }

  if (["draft", "open", "new"].includes(normalized)) {
    return "secondary";
  }

  return "default";
}

export function formatStatusLabel(status?: string | null) {
  return String(status || "unknown")
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}
