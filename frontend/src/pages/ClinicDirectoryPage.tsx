import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Building2, MapPin, Search as SearchIcon } from "lucide-react";

import type { ClinicSummary } from "@/types";
import { fetchCities, fetchClinics } from "@/lib/api";
import { sourceLabel } from "@/lib/format";
import { useDebounce } from "@/hooks/useDebounce";
import { cn } from "@/components/ui/utils";
import { AppShell } from "@/components/AppShell";
import { ClinicAvatar } from "@/components/ClinicAvatar";
import { RatingBadge } from "@/components/RatingBadge";
import { Pager } from "@/components/Pager";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
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

const PAGE_SIZE = 24;
const ALL = "all";
const SOURCES = ["kdl_olymp", "doq", "invitro", "helix"];
const SORTS: { key: "name" | "rating" | "services"; label: string }[] = [
  { key: "name", label: "По названию" },
  { key: "rating", label: "По рейтингу" },
  { key: "services", label: "Больше услуг" },
];

function clinicWord(n: number): string {
  const m10 = n % 10;
  const m100 = n % 100;
  if (m10 === 1 && m100 !== 11) return "клиника";
  if (m10 >= 2 && m10 <= 4 && (m100 < 10 || m100 >= 20)) return "клиники";
  return "клиник";
}

export function ClinicDirectoryPage() {
  const navigate = useNavigate();
  const [input, setInput] = useState("");
  const q = useDebounce(input, 300);
  const [city, setCity] = useState<string>(ALL);
  const [source, setSource] = useState<string>(ALL);
  const [sort, setSort] = useState<"name" | "rating" | "services">("name");
  const [page, setPage] = useState(1);

  useEffect(() => setPage(1), [q, city, source, sort]);

  const citiesQuery = useQuery({ queryKey: ["cities"], queryFn: fetchCities });
  const cityNames = citiesQuery.data?.map((c) => c.name) ?? [];

  const clinicsQuery = useQuery({
    queryKey: ["clinics", q, city, source, sort, page],
    queryFn: () =>
      fetchClinics({
        q: q.trim() || undefined,
        city: city === ALL ? undefined : city,
        source: source === ALL ? undefined : source,
        sort,
        limit: PAGE_SIZE,
        offset: (page - 1) * PAGE_SIZE,
      }),
  });

  const data = clinicsQuery.data;
  const items = data?.items ?? [];
  const total = data?.total ?? 0;
  const totalPages = useMemo(() => Math.max(1, Math.ceil(total / PAGE_SIZE)), [total]);

  const open = (id: number) => navigate(`/clinics/${id}`);

  return (
    <AppShell breadcrumb={[{ label: "Поиск", href: "/search" }, { label: "Клиники" }]}>
      <div className="mx-auto w-full max-w-[1400px] px-4 py-8 lg:px-6">
        <header className="mb-5">
          <h1 className="flex items-center gap-2 text-xl font-semibold text-foreground">
            <Building2 className="h-5 w-5 text-primary" /> Клиники
          </h1>
        </header>

        <div className="mb-4 flex flex-col gap-2.5 sm:flex-row sm:items-center">
          <div className="relative flex-1">
            <SearchIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-faintest" />
            <Input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Название клиники…"
              className="pl-9"
            />
          </div>
          <div className="grid grid-cols-2 gap-2 sm:flex sm:gap-2">
            <FilterSelect
              value={city}
              onChange={setCity}
              allLabel="Все города"
              options={cityNames}
              className="w-full sm:w-auto"
            />
            <FilterSelect
              value={source}
              onChange={setSource}
              allLabel="Все источники"
              options={SOURCES}
              labelFor={sourceLabel}
              className="w-full sm:w-auto"
            />
            <div className="col-span-2 sm:contents">
              <Select value={sort} onValueChange={(v) => setSort(v as typeof sort)}>
                <SelectTrigger size="sm" className="w-full gap-1.5 sm:w-auto">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent align="end">
                  {SORTS.map((s) => (
                    <SelectItem key={s.key} value={s.key}>
                      {s.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>

        <div className="mb-3 text-sm text-muted-foreground">
          <span className="font-semibold text-foreground">{total}</span> {clinicWord(total)}
        </div>

        {clinicsQuery.isLoading && <DirectorySkeleton />}

        {clinicsQuery.isSuccess && items.length === 0 && (
          <p className="rounded-xl border border-border bg-card p-8 text-center text-sm text-muted-foreground">
            Клиники не найдены.
          </p>
        )}

        {items.length > 0 && (
          <>
            {/* Desktop: table */}
            <div className="hidden overflow-hidden rounded-2xl border border-border bg-white shadow-sm md:block">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Клиника</TableHead>
                    <TableHead>Источник</TableHead>
                    <TableHead className="text-center">Города</TableHead>
                    <TableHead className="text-center">Филиалов</TableHead>
                    <TableHead className="text-center">Услуг</TableHead>
                    <TableHead>Рейтинг</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((c) => (
                    <TableRow
                      key={c.id}
                      onClick={() => open(c.id)}
                      className="cursor-pointer"
                    >
                      <TableCell>
                        <div className="flex items-center gap-3">
                          <ClinicAvatar name={c.name} size="sm" />
                          <span className="font-medium text-foreground">{c.name}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge variant="secondary">{sourceLabel(c.source_name)}</Badge>
                      </TableCell>
                      <TableCell className="text-center text-muted-foreground">
                        {c.cities.length}
                      </TableCell>
                      <TableCell className="text-center text-muted-foreground">
                        {c.branches_count}
                      </TableCell>
                      <TableCell className="text-center font-medium text-foreground">
                        {c.active_services_count.toLocaleString("ru-RU")}
                      </TableCell>
                      <TableCell>
                        {c.rating != null && (
                          <RatingBadge rating={c.rating} reviewsCount={c.reviews_count} />
                        )}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            {/* Mobile: cards */}
            <div className="grid gap-3 md:hidden">
              {items.map((c) => (
                <ClinicRowCard key={c.id} clinic={c} onClick={() => open(c.id)} />
              ))}
            </div>

            {totalPages > 1 && (
              <div className="mt-5">
                <Pager page={page} totalPages={totalPages} onPage={setPage} />
              </div>
            )}
          </>
        )}
      </div>
    </AppShell>
  );
}

function FilterSelect({
  value,
  onChange,
  allLabel,
  options,
  labelFor,
  className,
}: {
  value: string;
  onChange: (v: string) => void;
  allLabel: string;
  options: string[];
  labelFor?: (v: string) => string;
  className?: string;
}) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger size="sm" className={cn("gap-1.5", className ?? "w-auto")}>
        <SelectValue />
      </SelectTrigger>
      <SelectContent align="end" className="max-h-72">
        <SelectItem value={ALL}>{allLabel}</SelectItem>
        {options.map((o) => (
          <SelectItem key={o} value={o}>
            {labelFor ? labelFor(o) : o}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );
}

function ClinicRowCard({
  clinic,
  onClick,
}: {
  clinic: ClinicSummary;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className="flex flex-col gap-3 rounded-2xl border border-border bg-white p-4 text-left shadow-sm transition-colors hover:border-primary/40"
    >
      <div className="flex items-center gap-3">
        <ClinicAvatar name={clinic.name} size="sm" />
        <div className="min-w-0 flex-1">
          <div className="truncate font-semibold text-foreground">{clinic.name}</div>
          <Badge variant="secondary" className="mt-0.5">
            {sourceLabel(clinic.source_name)}
          </Badge>
        </div>
        {clinic.rating != null && (
          <RatingBadge rating={clinic.rating} reviewsCount={clinic.reviews_count} />
        )}
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
        <span className="flex items-center gap-1">
          <MapPin className="h-3.5 w-3.5" /> {clinic.cities.length} городов
        </span>
        <span>{clinic.branches_count} филиалов</span>
        <span className="font-medium text-foreground">
          {clinic.active_services_count.toLocaleString("ru-RU")} услуг
        </span>
      </div>
    </button>
  );
}

function DirectorySkeleton() {
  return (
    <div className="space-y-3 rounded-2xl border border-border bg-white p-4 shadow-sm">
      {Array.from({ length: 8 }).map((_, i) => (
        <div key={i} className="flex items-center gap-3">
          <Skeleton className="h-8 w-8 rounded-full" />
          <Skeleton className="h-4 w-48" />
          <Skeleton className="ml-auto h-4 w-24" />
        </div>
      ))}
    </div>
  );
}
