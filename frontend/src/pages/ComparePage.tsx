import { Link, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { ExternalLink } from "lucide-react";

import type { CompareRow } from "@/types";
import { fetchCompare } from "@/lib/api";
import { parseClinicIds } from "@/lib/compare";
import { formatPrice } from "@/lib/format";
import { cn } from "@/components/ui/utils";
import { ClinicAvatar } from "@/components/ClinicAvatar";
import { StatusBadge } from "@/components/StatusBadge";
import { AppShell } from "@/components/AppShell";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

function durationLabel(min: number | null, max: number | null): string {
  if (min == null && max == null) return "–";
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
    <AppShell breadcrumb={[{ label: "Поиск", href: "/" }, { label: "Сравнение" }]}>
      <div className="mx-auto max-w-5xl px-4 py-6 lg:px-6">
        {!enabled && (
          <p className="text-sm text-muted-foreground">
            Выберите услугу и клиники для сравнения.
          </p>
        )}
        {compareQuery.isLoading && (
          <div className="space-y-4">
            <Skeleton className="h-7 w-64" />
            <div className="grid grid-cols-3 gap-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <div
                  key={i}
                  className="space-y-3 rounded-xl border border-border bg-card p-5 shadow-sm"
                >
                  <Skeleton className="h-4 w-24" />
                  <Skeleton className="h-8 w-28" />
                  <Skeleton className="h-3 w-full" />
                  <Skeleton className="h-3 w-2/3" />
                </div>
              ))}
            </div>
          </div>
        )}

        {data && (
          <>
            <div className="mb-6 flex items-start justify-between gap-4">
              <div>
                <h1 className="text-xl font-semibold text-foreground">
                  Сравнение клиник · {data.service_name}
                </h1>
              </div>
              {diff > 0 && (
                <div className="shrink-0 rounded-xl bg-success-soft px-4 py-2 text-sm font-semibold text-success">
                  Экономия до {formatPrice(diff)}
                </div>
              )}
            </div>

            <div className="overflow-x-auto rounded-2xl border border-border bg-white shadow-sm">
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
                    <TableRow key={r.clinic_id} className={cn(r.is_cheapest && "bg-success-soft/50")}>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <ClinicAvatar name={r.clinic_name} size="sm" />
                          <span className="font-medium text-foreground">
                            {r.clinic_name}
                          </span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div
                          className={cn(
                            "text-lg font-bold leading-none",
                            r.is_cheapest ? "text-success" : "text-foreground",
                          )}
                        >
                          {formatPrice(r.price_kzt)}
                        </div>
                        {r.is_cheapest && (
                          <div className="mt-1">
                            <StatusBadge variant="success">Лучшая цена</StatusBadge>
                          </div>
                        )}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {r.city ?? "–"}
                      </TableCell>
                      <TableCell className="text-muted-foreground">
                        {durationLabel(r.duration_min, r.duration_max)}
                      </TableCell>
                      <TableCell>
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

            <div className="mt-4 flex justify-end">
              <Link
                to="/"
                className="rounded-xl border border-border px-5 py-2.5 text-sm text-muted-foreground transition-colors hover:bg-white"
              >
                ← Назад к поиску
              </Link>
            </div>
          </>
        )}
      </div>
    </AppShell>
  );
}
