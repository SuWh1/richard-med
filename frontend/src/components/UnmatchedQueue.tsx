import { useEffect, useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";
import { ArrowRight } from "lucide-react";

import { fetchUnmatched } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const PAGE_SIZE = 15;
const STATUSES = [
  { value: "pending", label: "Ожидают (серая зона)" },
  { value: "deferred", label: "Отложены (AI не уверен)" },
  { value: "added", label: "Добавлены как новые" },
  { value: "matched", label: "Сопоставлены (алиас)" },
];

export function UnmatchedQueue({ busy = false }: { busy?: boolean }) {
  const [status, setStatus] = useState("pending");
  const [offset, setOffset] = useState(0);

  useEffect(() => setOffset(0), [status]);

  const query = useQuery({
    queryKey: ["unmatched", status, offset],
    queryFn: () => fetchUnmatched({ status, limit: PAGE_SIZE, offset }),
    placeholderData: keepPreviousData,
    refetchInterval: busy ? 2000 : false,
  });

  const total = query.data?.total ?? 0;
  const items = query.data?.items ?? [];
  const from = total === 0 ? 0 : offset + 1;
  const to = Math.min(offset + PAGE_SIZE, total);

  return (
    <div className="rounded-xl border border-slate-200 bg-white shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-100 px-4 py-3">
        <div>
          <h2 className="font-semibold text-slate-900">Очередь на сопоставление</h2>
          <p className="text-xs text-slate-500">
            Сырое название · кандидат каталога · уверенность — {total.toLocaleString("ru-RU")}
          </p>
        </div>
        <Select value={status} onValueChange={setStatus}>
          <SelectTrigger className="h-9 w-[220px]">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {STATUSES.map((s) => (
              <SelectItem key={s.value} value={s.value}>
                {s.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Сырое название (источник)</TableHead>
            <TableHead>Кандидат каталога</TableHead>
            <TableHead className="text-right">Уверенность</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.map((row) => (
            <TableRow key={row.id}>
              <TableCell
                className="max-w-[320px] truncate font-medium text-slate-900"
                title={row.raw_name}
              >
                {row.raw_name}
              </TableCell>
              <TableCell className="max-w-[300px] truncate text-slate-600">
                {row.suggested_name ? (
                  <span className="flex items-center gap-1.5" title={row.suggested_name}>
                    <ArrowRight className="h-3.5 w-3.5 shrink-0 text-slate-300" />
                    {row.suggested_name}
                  </span>
                ) : (
                  <span className="text-slate-400">— нет похожих</span>
                )}
              </TableCell>
              <TableCell className="text-right">
                <ConfidenceBadge value={row.confidence} />
              </TableCell>
            </TableRow>
          ))}
          {items.length === 0 && !query.isLoading ? (
            <TableRow>
              <TableCell colSpan={3} className="py-6 text-center text-sm text-slate-500">
                Очередь пуста.
              </TableCell>
            </TableRow>
          ) : null}
        </TableBody>
      </Table>

      <div className="flex items-center justify-between border-t border-slate-100 px-4 py-3 text-sm text-slate-500">
        <span>
          {from}–{to} из {total.toLocaleString("ru-RU")}
        </span>
        <div className="flex gap-2">
          <button
            onClick={() => setOffset((o) => Math.max(0, o - PAGE_SIZE))}
            disabled={offset === 0}
            className="rounded-lg border border-slate-200 px-3 py-1 transition hover:bg-slate-50 disabled:opacity-40"
          >
            Назад
          </button>
          <button
            onClick={() => setOffset((o) => o + PAGE_SIZE)}
            disabled={to >= total}
            className="rounded-lg border border-slate-200 px-3 py-1 transition hover:bg-slate-50 disabled:opacity-40"
          >
            Вперёд
          </button>
        </div>
      </div>
    </div>
  );
}

function ConfidenceBadge({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  // Gray zone is 75–88%; warmer colour = closer to the auto-match threshold.
  const tone =
    pct >= 85
      ? "bg-emerald-100 text-emerald-800"
      : pct >= 80
        ? "bg-amber-100 text-amber-800"
        : "bg-slate-100 text-slate-600";
  return <Badge className={`tabular-nums ${tone}`}>{pct}%</Badge>;
}
