import { format, formatDistanceToNowStrict, parseISO } from "date-fns";

export function formatDateTime(value?: string | null, fallback = "—") {
  if (!value) {
    return fallback;
  }

  try {
    return format(parseISO(value), "PPpp");
  } catch {
    return value;
  }
}

export function formatRelativeDate(value?: string | null, fallback = "—") {
  if (!value) {
    return fallback;
  }

  try {
    return formatDistanceToNowStrict(parseISO(value), { addSuffix: true });
  } catch {
    return value;
  }
}
