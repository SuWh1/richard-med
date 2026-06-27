import { useEffect, useState } from "react";
import { keepPreviousData, useQuery } from "@tanstack/react-query";

import { fetchCatalogServices } from "@/lib/api";
import { useDebounce } from "@/hooks/useDebounce";
import { Input } from "@/components/ui/input";
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
const ALL = "__all__";
const REVIEW_CATEGORY = "прочее";
const CATEGORIES = [
  "лаборатория",
  "приём врача",
  "диагностика",
  "процедура",
  REVIEW_CATEGORY,
];

export function ServicesTable({ busy = false }: { busy?: boolean }) {
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("");
  const [offset, setOffset] = useState(0);
  const q = useDebounce(search.trim(), 250);

  // Any filter change returns to the first page.
  useEffect(() => setOffset(0), [q, category]);

  const query = useQuery({
    queryKey: ["catalog-services", q, category, offset],
    queryFn: () =>
      fetchCatalogServices({
        q: q || undefined,
        category: category || undefined,
        limit: PAGE_SIZE,
        offset,
      }),
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
          <h2 className="font-semibold text-slate-900">Каталог услуг</h2>
          <p className="text-xs text-slate-500">
            Живой нормализованный каталог · {total.toLocaleString("ru-RU")} услуг
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Поиск услуги…"
            className="h-9 w-[200px]"
          />
          <Select
            value={category || ALL}
            onValueChange={(v) => setCategory(v === ALL ? "" : v)}
          >
            <SelectTrigger className="h-9 w-[160px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL}>Все категории</SelectItem>
              {CATEGORIES.map((c) => (
                <SelectItem key={c} value={c}>
                  {c}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Услуга</TableHead>
            <TableHead>Категория</TableHead>
            <TableHead>Источник</TableHead>
            <TableHead className="text-right">Синонимы</TableHead>
            <TableHead className="text-right">Цены</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {items.map((row) => (
            <TableRow key={row.id}>
              <TableCell
                className="max-w-[320px] truncate font-medium text-slate-900"
                title={row.name_ru}
              >
                {row.name_ru}
              </TableCell>
              <TableCell>
                {row.category === REVIEW_CATEGORY ? (
                  <Badge className="bg-amber-100 text-amber-800">на проверку</Badge>
                ) : (
                  <span className="text-slate-600">{row.category}</span>
                )}
              </TableCell>
              <TableCell>
                {row.origin === "auto" ? (
                  <Badge className="bg-amber-100 text-amber-800">AI</Badge>
                ) : (
                  <Badge variant="secondary">каталог</Badge>
                )}
              </TableCell>
              <TableCell className="text-right tabular-nums text-slate-600">
                {row.alias_count}
              </TableCell>
              <TableCell className="text-right tabular-nums font-semibold text-slate-900">
                {row.price_count}
              </TableCell>
            </TableRow>
          ))}
          {items.length === 0 && !query.isLoading ? (
            <TableRow>
              <TableCell colSpan={5} className="py-6 text-center text-sm text-slate-500">
                Ничего не найдено.
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
