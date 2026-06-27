import { Link, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ExternalLink } from "lucide-react";

import type { CompareRow } from "@/types";
import { fetchCompare } from "@/lib/api";
import { parseClinicIds } from "@/lib/compare";
import { formatPrice } from "@/lib/format";
import { cn } from "@/components/ui/utils";
import { FreshBadge } from "@/components/FreshBadge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

function durationLabel(min: number | null, max: number | null): string {
  if (min == null && max == null) return "—";
  if (min != null && max != null && min !== max) return `${min}–${max} дн.`;
  return `${max ?? min} дн.`;
}

function savings(rows: CompareRow[]): number {
  if (rows.length < 2) return 0;
  const prices = rows.map((r) => r.price_kzt);
  return Math.max(...prices) - Math.min(...prices);
}

export function ComparePage() {
  const [params] = useSearchParams();
  const serviceId = Number(params.get("service_id"));
  const clinicIds = parseClinicIds(params.get("clinic_ids"));
  const enabled = Number.isInteger(serviceId) && serviceId > 0 && clinicIds.length > 0;

  const compareQuery = useQuery({
    queryKey: ["compare", serviceId, clinicIds.join(",")],
    queryFn: () => fetchCompare(serviceId, clinicIds),
    enabled,
  });

  const data = compareQuery.data;
  const diff = data ? savings(data.rows) : 0;

  return (
    <div className="mx-auto max-w-4xl px-4 py-8">
      <Link to="/" className="text-sm font-medium text-primary hover:underline">
        ← К поиску
      </Link>

      {!enabled && (
        <p className="mt-6 text-sm text-muted-foreground">
          Выберите услугу и клиники для сравнения.
        </p>
      )}
      {compareQuery.isLoading && (
        <p className="mt-6 text-sm text-muted-foreground">Загрузка…</p>
      )}

      {data && (
        <>
          <header className="mt-4">
            <h1 className="text-xl font-semibold text-foreground">
              Сравнение: {data.service_name}
            </h1>
            {diff > 0 && (
              <p className="text-sm text-muted-foreground">
                Экономия до{" "}
                <span className="font-semibold text-primary">{formatPrice(diff)}</span> между
                клиниками
              </p>
            )}
          </header>

          <div className="mt-6 overflow-hidden rounded-xl border border-border bg-white">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Клиника</TableHead>
                  <TableHead>Цена</TableHead>
                  <TableHead>Город</TableHead>
                  <TableHead>Срок</TableHead>
                  <TableHead>Обновлено</TableHead>
                  <TableHead>Источник</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {data.rows.map((r) => (
                  <TableRow key={r.clinic_id}>
                    <TableCell className="font-medium text-foreground">
                      {r.clinic_name}
                    </TableCell>
                    <TableCell
                      className={cn(
                        "font-bold",
                        r.is_cheapest ? "bg-[#DCFCE7] text-[#16A34A]" : "text-foreground",
                      )}
                    >
                      {formatPrice(r.price_kzt)}
                    </TableCell>
                    <TableCell className="text-muted-foreground">{r.city ?? "—"}</TableCell>
                    <TableCell className="text-muted-foreground">
                      {durationLabel(r.duration_min, r.duration_max)}
                    </TableCell>
                    <TableCell>
                      <FreshBadge freshness={r.freshness} ageDays={r.age_days} />
                    </TableCell>
                    <TableCell>
                      <a
                        href={r.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
                      >
                        Открыть <ExternalLink className="h-3 w-3" />
                      </a>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </>
      )}
    </div>
  );
}
