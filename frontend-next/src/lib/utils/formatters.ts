export function formatNumber(value?: number | null) {
  return new Intl.NumberFormat("en-US").format(Number(value || 0));
}

export function formatBytes(value?: number | null) {
  const size = Number(value || 0);
  if (size < 1024) {
    return `${size} B`;
  }

  const units = ["KB", "MB", "GB"];
  let next = size / 1024;
  let index = 0;
  while (next >= 1024 && index < units.length - 1) {
    next /= 1024;
    index += 1;
  }

  return `${next.toFixed(1)} ${units[index]}`;
}

export function titleCase(value?: string | null) {
  return String(value || "")
    .replace(/[_-]+/g, " ")
    .replace(/\b\w/g, (char) => char.toUpperCase());
}
