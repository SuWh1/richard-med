import { formatPrice } from "@/lib/format";

export function PriceRangeBar({
  min,
  max,
  avg,
  median,
}: {
  min: number;
  max: number;
  avg: number;
  median: number;
}) {
  const span = max - min || 1;
  const pct = (value: number) => ((value - min) / span) * 100;

  return (
    <div className="flex flex-col gap-1">
      <div className="relative h-2 rounded-full bg-gradient-to-r from-emerald-400 via-amber-300 to-rose-400">
        <Marker position={pct(median)} color="bg-slate-900" title="Медиана" />
        <Marker position={pct(avg)} color="bg-sky-600" title="Среднее" />
      </div>
      <div className="flex justify-between text-xs text-slate-500">
        <span className="font-medium text-emerald-700">{formatPrice(min)}</span>
        <span className="font-medium text-rose-700">{formatPrice(max)}</span>
      </div>
    </div>
  );
}

function Marker({
  position,
  color,
  title,
}: {
  position: number;
  color: string;
  title: string;
}) {
  return (
    <span
      title={title}
      className={`absolute top-1/2 h-3.5 w-1 -translate-x-1/2 -translate-y-1/2 rounded-full ${color}`}
      style={{ left: `${position}%` }}
    />
  );
}
