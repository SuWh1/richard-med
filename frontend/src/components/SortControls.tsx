import type { SortKey } from "@/types";

const OPTIONS: { key: SortKey; label: string }[] = [
  { key: "best_value", label: "Оптимальные" },
  { key: "cheapest", label: "Дешевле" },
  { key: "newest", label: "Свежее" },
];

export function SortControls({
  sort,
  onChange,
  includeStale,
  onToggleStale,
}: {
  sort: SortKey;
  onChange: (s: SortKey) => void;
  includeStale: boolean;
  onToggleStale: (v: boolean) => void;
}) {
  return (
    <div className="flex flex-wrap items-center justify-between gap-3">
      <div className="inline-flex rounded-lg border border-slate-200 bg-white p-0.5">
        {OPTIONS.map((opt) => (
          <button
            key={opt.key}
            onClick={() => onChange(opt.key)}
            className={`rounded-md px-3 py-1.5 text-sm font-medium transition ${
              sort === opt.key
                ? "bg-slate-900 text-white"
                : "text-slate-600 hover:text-slate-900"
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>
      <label className="flex items-center gap-2 text-sm text-slate-600">
        <input
          type="checkbox"
          checked={includeStale}
          onChange={(e) => onToggleStale(e.target.checked)}
          className="h-4 w-4 rounded border-slate-300"
        />
        Показать устаревшие
      </label>
    </div>
  );
}
