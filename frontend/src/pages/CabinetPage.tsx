import { type ReactNode } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowDownRight,
  ArrowUpRight,
  Bell,
  BellOff,
  Bookmark,
  Check,
  LogOut,
  Search,
  Trash2,
} from "lucide-react";

import type {
  PriceNotification,
  SavedServiceWatch,
  SearchHistoryItem,
} from "@/types";
import {
  deleteCabinetService,
  fetchCabinet,
  markCabinetServiceSeen,
  toggleCabinetService,
} from "@/lib/api";
import { logout } from "@/lib/auth-client";
import { formatDateTime, formatPrice } from "@/lib/format";
import { useAuth } from "@/lib/useAuth";
import { searchHref } from "@/hooks/useSearchState";
import { AppShell } from "@/components/AppShell";
import { ClinicAvatar } from "@/components/ClinicAvatar";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/components/ui/utils";

function plural(n: number, [one, few, many]: [string, string, string]): string {
  const mod10 = n % 10;
  const mod100 = n % 100;
  if (mod10 === 1 && mod100 !== 11) return one;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return few;
  return many;
}

function firstName(name: string | null | undefined, email: string | undefined): string {
  const fromName = (name ?? "").trim().split(/\s+/)[0];
  if (fromName) return fromName;
  return (email ?? "").split("@")[0] || "Пользователь";
}

type TrendDir = "down" | "up" | "flat" | "none";

function priceTrend(watch: SavedServiceWatch): { dir: TrendDir; delta: number } {
  const { current_min_price: current, baseline_min_price: baseline } = watch;
  if (current == null || baseline == null) return { dir: "none", delta: 0 };
  const delta = current - baseline;
  if (delta < 0) return { dir: "down", delta };
  if (delta > 0) return { dir: "up", delta };
  return { dir: "flat", delta: 0 };
}

export function CabinetPage() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user, isAdmin } = useAuth();

  const cabinetQuery = useQuery({
    queryKey: ["cabinet"],
    queryFn: fetchCabinet,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ["cabinet"] });
  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteCabinetService(id),
    onSuccess: invalidate,
  });
  const toggleMutation = useMutation({
    mutationFn: ({ id, enabled }: { id: number; enabled: boolean }) =>
      toggleCabinetService(id, enabled),
    onSuccess: invalidate,
  });
  const markSeenMutation = useMutation({
    mutationFn: (id: number) => markCabinetServiceSeen(id),
    onSuccess: invalidate,
  });

  const onLogout = () => {
    logout();
    navigate("/");
  };

  const dashboard = cabinetQuery.data;
  const saved = dashboard?.saved_services ?? [];
  const notifications = dashboard?.notifications ?? [];
  const history = dashboard?.recent_searches ?? [];
  const cityCount = new Set(saved.map((s) => s.city)).size;

  return (
    <AppShell breadcrumb={[{ label: "Поиск", href: "/search" }, { label: "Кабинет" }]}>
      <div className="mx-auto w-full max-w-[940px] px-4 py-8 sm:px-6 lg:py-10">
        <Greeting
          name={firstName(user?.name, user?.email)}
          email={user?.email}
          isAdmin={isAdmin}
          savedCount={saved.length}
          cityCount={cityCount}
          notifyCount={notifications.length}
          loading={cabinetQuery.isLoading}
          onLogout={onLogout}
        />

        {cabinetQuery.isLoading && <CabinetSkeleton />}

        {cabinetQuery.isError && (
          <div className="mt-8 rounded-2xl border border-danger/30 bg-danger-soft/40 p-6">
            <div className="font-semibold text-foreground">Не удалось загрузить кабинет</div>
            <p className="mt-1 text-sm text-muted-foreground">
              Проверьте соединение и повторите.
            </p>
            <Button
              className="mt-4"
              variant="outline"
              size="sm"
              onClick={() => cabinetQuery.refetch()}
            >
              Повторить
            </Button>
          </div>
        )}

        {dashboard && (
          <div className="mt-8 space-y-10">
            <PriceAlerts
              notifications={notifications}
              watchCount={saved.length}
              onMarkSeen={(id) => markSeenMutation.mutate(id)}
              pendingId={markSeenMutation.variables}
            />

            <Watchlist
              watches={saved}
              onDelete={(id) => deleteMutation.mutate(id)}
              onToggle={(id, enabled) => toggleMutation.mutate({ id, enabled })}
              pendingDeleteId={deleteMutation.variables}
              pendingToggleId={toggleMutation.variables?.id}
            />

            <RecentSearches items={history} />
          </div>
        )}
      </div>
    </AppShell>
  );
}

interface GreetingProps {
  name: string;
  email: string | undefined;
  isAdmin: boolean;
  savedCount: number;
  cityCount: number;
  notifyCount: number;
  loading: boolean;
  onLogout: () => void;
}

function Greeting({
  name,
  email,
  isAdmin,
  savedCount,
  cityCount,
  notifyCount,
  loading,
  onLogout,
}: GreetingProps) {
  const summary = loading
    ? "Загружаем ваши отслеживаемые услуги…"
    : savedCount === 0
      ? "Сохраняйте услуги из поиска. Мы будем следить за ценами за вас."
      : `Вы отслеживаете ${savedCount} ${plural(savedCount, [
          "услугу",
          "услуги",
          "услуг",
        ])} в ${cityCount} ${plural(cityCount, ["городе", "городах", "городах"])}.` +
        (notifyCount > 0
          ? ` ${notifyCount} ${plural(notifyCount, ["цена изменилась", "цены изменились", "цен изменилось"])} с прошлого визита.`
          : " Цены пока без изменений.");

  return (
    <header className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">
      <div className="min-w-0">
        <h1 className="text-2xl font-semibold tracking-tight text-foreground text-balance sm:text-[28px]">
          С возвращением, {name}
        </h1>
        <p className="mt-2 max-w-[58ch] text-[15px] leading-relaxed text-muted-foreground text-pretty">
          {summary}
        </p>
      </div>

      <div className="flex shrink-0 items-center gap-3 rounded-xl border border-border bg-card px-3 py-2.5 shadow-sm">
        <ClinicAvatar name={name || email || "?"} size="md" />
        <div className="min-w-0 max-w-[160px]">
          <div className="flex items-center gap-1.5">
            <span className="truncate text-sm font-semibold text-foreground">{name}</span>
            {isAdmin && (
              <span className="shrink-0 rounded-full bg-accent px-1.5 py-0.5 text-[10px] font-medium text-accent-foreground">
                Админ
              </span>
            )}
          </div>
          <div className="truncate text-xs text-muted-foreground">{email}</div>
        </div>
        <button
          type="button"
          onClick={onLogout}
          title="Выйти"
          aria-label="Выйти"
          className="shrink-0 rounded-lg p-2 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
        >
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    </header>
  );
}

function PriceAlerts({
  notifications,
  watchCount,
  onMarkSeen,
  pendingId,
}: {
  notifications: PriceNotification[];
  watchCount: number;
  onMarkSeen: (watchId: number) => void;
  pendingId?: number;
}) {
  if (notifications.length === 0) {
    if (watchCount === 0) return null;
    return (
      <section
        aria-label="Изменения цен"
        className="flex items-center gap-3 rounded-xl border border-border bg-secondary/40 px-4 py-3"
      >
        <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-success-soft text-success">
          <Check className="h-4 w-4" />
        </span>
        <p className="text-sm text-muted-foreground">
          Изменений цен нет. Мы следим за вашими услугами и сообщим, когда станет дешевле.
        </p>
      </section>
    );
  }

  return (
    <section aria-label="Изменения цен" className="space-y-3">
      <SectionHeading title="Изменения цен" count={notifications.length} />
      <div className="space-y-3">
        {notifications.map((n, i) => {
          const cheaper = n.delta_kzt < 0;
          return (
            <article
              key={n.watch_id}
              style={{ animationDelay: `${Math.min(i, 6) * 50}ms` }}
              className={cn(
                "flex flex-col gap-4 rounded-2xl border p-4 duration-300 animate-in fade-in slide-in-from-bottom-1 sm:flex-row sm:items-center sm:p-5",
                cheaper
                  ? "border-success/25 bg-success-soft/40"
                  : "border-warning/30 bg-warning-soft/40",
              )}
            >
              <span
                className={cn(
                  "flex h-12 w-12 shrink-0 items-center justify-center rounded-xl",
                  cheaper ? "bg-success/15 text-success" : "bg-warning/15 text-warning-strong",
                )}
              >
                {cheaper ? (
                  <ArrowDownRight className="h-6 w-6" />
                ) : (
                  <ArrowUpRight className="h-6 w-6" />
                )}
              </span>

              <div className="min-w-0 flex-1">
                <div className="truncate font-semibold text-foreground">{n.service_name}</div>
                <div className="mt-0.5 flex flex-wrap items-baseline gap-x-2 text-sm">
                  <span className="text-muted-foreground">{n.city}:</span>
                  <span className="text-muted-foreground line-through">
                    {formatPrice(n.previous_min_price)}
                  </span>
                  <span className="font-semibold tabular-nums text-foreground">
                    {formatPrice(n.current_min_price)}
                  </span>
                  <span
                    className={cn(
                      "rounded-full px-2 py-0.5 text-xs font-semibold tabular-nums",
                      cheaper ? "bg-success/15 text-success" : "bg-warning/20 text-warning-strong",
                    )}
                  >
                    {n.delta_kzt > 0 ? "+" : "−"}
                    {formatPrice(Math.abs(n.delta_kzt))} · {n.delta_pct > 0 ? "+" : ""}
                    {n.delta_pct}%
                  </span>
                </div>
              </div>

              <div className="flex shrink-0 gap-2">
                <Button asChild size="sm">
                  <Link to={searchHref({ q: n.service_name, city: n.city })}>Посмотреть</Link>
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  disabled={pendingId === n.watch_id}
                  onClick={() => onMarkSeen(n.watch_id)}
                  title="Отметить просмотренным"
                  aria-label="Отметить просмотренным"
                >
                  <Check className="h-4 w-4" />
                </Button>
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}

function Watchlist({
  watches,
  onDelete,
  onToggle,
  pendingDeleteId,
  pendingToggleId,
}: {
  watches: SavedServiceWatch[];
  onDelete: (watchId: number) => void;
  onToggle: (watchId: number, enabled: boolean) => void;
  pendingDeleteId?: number;
  pendingToggleId?: number;
}) {
  return (
    <section aria-label="Отслеживаемые услуги" className="space-y-3">
      <SectionHeading title="Отслеживаемые услуги" count={watches.length || undefined} />

      {watches.length === 0 ? (
        <EmptyState
          icon={<Bookmark className="h-5 w-5" />}
          title="Пока нет сохранённых услуг"
          body="Найдите услугу и нажмите «Сохранить». Мы соберём цены всех клиник города и сообщим об изменениях."
          action={
            <Button asChild size="sm">
              <Link to="/search">
                <Search className="h-4 w-4" /> Перейти к поиску
              </Link>
            </Button>
          }
        />
      ) : (
        <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
          <div className="hidden grid-cols-[minmax(0,1fr)_140px_88px] gap-4 border-b border-border px-5 py-2.5 text-xs font-medium uppercase tracking-wide text-faint sm:grid">
            <span>Услуга</span>
            <span className="text-right">Текущая цена</span>
            <span className="text-right">Уведомления</span>
          </div>
          <ul className="divide-y divide-border">
            {watches.map((watch, i) => (
              <WatchRow
                key={watch.id}
                watch={watch}
                index={i}
                onDelete={onDelete}
                onToggle={onToggle}
                deleting={pendingDeleteId === watch.id}
                toggling={pendingToggleId === watch.id}
              />
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}

function WatchRow({
  watch,
  index,
  onDelete,
  onToggle,
  deleting,
  toggling,
}: {
  watch: SavedServiceWatch;
  index: number;
  onDelete: (watchId: number) => void;
  onToggle: (watchId: number, enabled: boolean) => void;
  deleting: boolean;
  toggling: boolean;
}) {
  const trend = priceTrend(watch);
  const hasPrice = watch.current_min_price != null;

  return (
    <li
      style={{ animationDelay: `${Math.min(index, 8) * 40}ms` }}
      className="grid grid-cols-1 gap-3 px-5 py-4 duration-300 animate-in fade-in transition-colors hover:bg-secondary/30 sm:grid-cols-[minmax(0,1fr)_140px_88px] sm:items-center sm:gap-4"
    >
      <div className="min-w-0">
        <Link
          to={searchHref({ q: watch.service_name, city: watch.city })}
          className="block font-semibold text-foreground hover:text-primary [overflow-wrap:anywhere] line-clamp-2"
        >
          {watch.service_name}
        </Link>
        {watch.clinic_name && (
          <div className="mt-0.5 truncate text-sm font-medium text-foreground">
            {watch.clinic_name}
          </div>
        )}
        <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-0.5 text-xs text-muted-foreground">
          <span className="rounded-full bg-secondary px-2 py-0.5 font-medium text-secondary-foreground">
            {watch.category}
          </span>
          <span>{watch.city}</span>
          <span aria-hidden>·</span>
          {watch.clinic_name ? (
            <span>в этой клинике</span>
          ) : (
            <span>
              {watch.clinic_count}{" "}
              {plural(watch.clinic_count, ["клиника", "клиники", "клиник"])}
            </span>
          )}
          <span aria-hidden>·</span>
          <span>обновлено {formatDateTime(watch.updated_at)}</span>
        </div>
      </div>

      <div className="flex items-baseline justify-between sm:flex-col sm:items-end sm:justify-center sm:gap-0.5">
        <span className="text-xs text-muted-foreground sm:hidden">Текущая цена</span>
        <div className="text-right">
          <div className="font-semibold tabular-nums text-foreground">
            {hasPrice ? `от ${formatPrice(watch.current_min_price as number)}` : "Нет свежих цен"}
          </div>
          <TrendBadge trend={trend} />
        </div>
      </div>

      <div className="flex items-center gap-1 sm:justify-end">
        <Button
          variant="ghost"
          size="icon"
          disabled={toggling}
          title={watch.notify_enabled ? "Уведомления включены" : "Уведомления выключены"}
          aria-label={watch.notify_enabled ? "Отключить уведомления" : "Включить уведомления"}
          aria-pressed={watch.notify_enabled}
          onClick={() => onToggle(watch.id, !watch.notify_enabled)}
          className={watch.notify_enabled ? "text-primary" : "text-faint"}
        >
          {watch.notify_enabled ? <Bell className="h-4 w-4" /> : <BellOff className="h-4 w-4" />}
        </Button>
        <Button
          variant="ghost"
          size="icon"
          disabled={deleting}
          title="Удалить"
          aria-label="Удалить сохранённую услугу"
          onClick={() => onDelete(watch.id)}
          className="text-faint hover:text-danger"
        >
          <Trash2 className="h-4 w-4" />
        </Button>
      </div>
    </li>
  );
}

function TrendBadge({ trend }: { trend: { dir: TrendDir; delta: number } }) {
  if (trend.dir === "none") {
    return <span className="text-xs text-faint">следим за ценой</span>;
  }
  if (trend.dir === "flat") {
    return <span className="text-xs text-muted-foreground">без изменений</span>;
  }
  const cheaper = trend.dir === "down";
  return (
    <span
      className={cn(
        "inline-flex items-center gap-0.5 text-xs font-medium tabular-nums",
        cheaper ? "text-success" : "text-warning-strong",
      )}
    >
      {cheaper ? (
        <ArrowDownRight className="h-3.5 w-3.5" />
      ) : (
        <ArrowUpRight className="h-3.5 w-3.5" />
      )}
      {cheaper ? "−" : "+"}
      {formatPrice(Math.abs(trend.delta))}
    </span>
  );
}

function RecentSearches({ items }: { items: SearchHistoryItem[] }) {
  if (items.length === 0) {
    return (
      <section aria-label="Недавние поиски" className="space-y-3">
        <SectionHeading title="Недавние поиски" />
        <p className="text-sm text-muted-foreground">
          Здесь появятся ваши последние запросы, чтобы быстро к ним вернуться.
        </p>
      </section>
    );
  }

  return (
    <section aria-label="Недавние поиски" className="space-y-3">
      <SectionHeading title="Недавние поиски" />
      <div className="flex flex-wrap gap-2">
        {items.map((item) => (
          <Link
            key={item.id}
            to={searchHref({ q: item.service_name || item.q, city: item.city })}
            className="group inline-flex max-w-full items-center gap-2 rounded-full border border-border bg-card px-3 py-1.5 text-sm shadow-sm transition-colors hover:border-primary/40 hover:bg-accent/40"
          >
            <Search className="h-3.5 w-3.5 shrink-0 text-faint group-hover:text-primary" />
            <span className="truncate font-medium text-foreground">
              {item.service_name || item.q}
            </span>
            <span className="shrink-0 text-xs text-muted-foreground">{item.city}</span>
            <span className="shrink-0 rounded-full bg-secondary px-1.5 py-0.5 text-[11px] font-medium tabular-nums text-secondary-foreground">
              {item.result_count}
            </span>
          </Link>
        ))}
      </div>
    </section>
  );
}

function SectionHeading({ title, count }: { title: string; count?: number }) {
  return (
    <div className="flex items-center gap-2">
      <h2 className="text-base font-semibold text-foreground">{title}</h2>
      {count != null && (
        <span className="rounded-full bg-secondary px-2 py-0.5 text-xs font-medium tabular-nums text-secondary-foreground">
          {count}
        </span>
      )}
    </div>
  );
}

function EmptyState({
  icon,
  title,
  body,
  action,
}: {
  icon: ReactNode;
  title: string;
  body: string;
  action?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center gap-3 rounded-2xl border border-dashed border-border bg-secondary/30 px-6 py-10 text-center">
      <span className="flex h-11 w-11 items-center justify-center rounded-full bg-accent text-accent-foreground">
        {icon}
      </span>
      <div className="max-w-[44ch] space-y-1">
        <div className="font-semibold text-foreground">{title}</div>
        <p className="text-sm text-muted-foreground text-pretty">{body}</p>
      </div>
      {action}
    </div>
  );
}

function CabinetSkeleton() {
  return (
    <div className="mt-8 space-y-10">
      <Skeleton className="h-16 w-full rounded-xl" />
      <div className="space-y-3">
        <Skeleton className="h-5 w-48" />
        <div className="space-y-3 rounded-2xl border border-border p-2">
          {[0, 1, 2].map((i) => (
            <Skeleton key={i} className="h-16 w-full rounded-xl" />
          ))}
        </div>
      </div>
      <div className="space-y-3">
        <Skeleton className="h-5 w-40" />
        <div className="flex gap-2">
          <Skeleton className="h-8 w-40 rounded-full" />
          <Skeleton className="h-8 w-32 rounded-full" />
        </div>
      </div>
    </div>
  );
}
