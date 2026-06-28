export function formatPrice(kzt: number): string {
  return `${kzt.toLocaleString("ru-RU")} ₸`;
}

export function capitalize(text: string): string {
  if (!text) return text;
  return text.charAt(0).toUpperCase() + text.slice(1);
}

export function freshnessLabel(freshness: string, ageDays: number): string {
  if (freshness === "stale") return "Цена требует обновления";
  if (ageDays <= 0) return "Обновлено сегодня";
  if (ageDays === 1) return "Обновлено вчера";
  return `Обновлено ${ageDays} дн. назад`;
}

const SOURCE_LABELS: Record<string, string> = {
  kdl_olymp: "KDL Olymp",
  doq: "DOQ",
  invitro: "Invitro",
};

export function sourceLabel(name: string): string {
  return SOURCE_LABELS[name] ?? name;
}

export function formatDateTime(iso: string | null): string {
  if (!iso) return "–";
  return new Date(iso).toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatReviewDate(iso: string | null): string {
  if (!iso) return "";
  return new Date(iso).toLocaleDateString("ru-RU", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

export function formatDuration(sec: number | null): string {
  if (sec === null) return "–";
  if (sec < 60) return `${sec.toFixed(1)} с`;
  return `${Math.floor(sec / 60)} мин ${Math.round(sec % 60)} с`;
}
