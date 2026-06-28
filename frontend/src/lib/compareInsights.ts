import type { CompareRow } from "@/types";

export const ADVANTAGE = {
  price: "Самая низкая цена",
  fresh: "Самые свежие данные",
  fast: "Быстрый результат",
} as const;

export type Insights = Record<number, string[]>;

function effDuration(r: CompareRow): number | null {
  return r.duration_max ?? r.duration_min;
}

function tagWinners(
  rows: CompareRow[],
  value: (r: CompareRow) => number | null,
  label: string,
  result: Insights,
): void {
  const valued = rows
    .map((r) => ({ id: r.clinic_id, v: value(r) }))
    .filter((x): x is { id: number; v: number } => x.v != null);
  if (valued.length < 2) return;

  const min = Math.min(...valued.map((x) => x.v));
  const max = Math.max(...valued.map((x) => x.v));
  if (min >= max) return;

  for (const x of valued) {
    if (x.v === min) result[x.id].push(label);
  }
}

export function compareInsights(rows: CompareRow[]): Insights {
  const result: Insights = {};
  for (const r of rows) result[r.clinic_id] = [];
  if (rows.length < 2) return result;

  tagWinners(rows, (r) => r.price_kzt, ADVANTAGE.price, result);
  tagWinners(rows, (r) => r.age_days, ADVANTAGE.fresh, result);
  tagWinners(rows, effDuration, ADVANTAGE.fast, result);

  return result;
}
