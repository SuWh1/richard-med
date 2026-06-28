import { type MouseEvent, type ReactNode } from "react";
import { useQuery } from "@tanstack/react-query";
import { ExternalLink, FlaskConical, Stethoscope } from "lucide-react";

import type { SourcePublic } from "@/types";
import { fetchSources } from "@/lib/api";
import { cn } from "@/components/ui/utils";

type Variant = "hero" | "compact" | "wide";

function kindIcon(kind: string) {
  return kind.toLowerCase().includes("врач") ? Stethoscope : FlaskConical;
}

function variantOf(index: number, total: number): Variant {
  if (total < 4) return "compact";
  if (index === 0) return "hero";
  if (index === total - 1) return "wide";
  return "compact";
}

function trackSpotlight(e: MouseEvent<HTMLElement>) {
  const r = e.currentTarget.getBoundingClientRect();
  e.currentTarget.style.setProperty("--spot-x", `${e.clientX - r.left}px`);
  e.currentTarget.style.setProperty("--spot-y", `${e.clientY - r.top}px`);
}

const fmt = (n: number) => n.toLocaleString("ru-RU");

export function SourcesSection() {
  const { data, isLoading } = useQuery({ queryKey: ["sources"], queryFn: fetchSources });
  const sources = data ?? [];
  const bento = sources.length >= 4;

  return (
    <section id="sources" className="mx-auto w-full max-w-5xl scroll-mt-24 px-4 py-20">
      <div className="mb-10 text-center">
        <span className="mb-3 inline-block rounded-full bg-accent px-3 py-1 text-xs font-semibold uppercase tracking-wider text-accent-foreground">
          Прозрачность
        </span>
        <h2 className="text-3xl font-semibold tracking-tight text-foreground">
          Источники данных
        </h2>
        <p className="mx-auto mt-3 max-w-xl text-muted-foreground">
          Цены собираются с официальных сайтов клиник и лабораторий — каждую можно
          проверить по ссылке.
        </p>
      </div>

      {isLoading ? (
        <div className="grid gap-4 sm:grid-cols-3 sm:grid-rows-2">
          <div className="animate-pulse rounded-3xl border border-border bg-card sm:col-span-2 sm:row-span-2 sm:min-h-[20rem]" />
          <div className="h-40 animate-pulse rounded-3xl border border-border bg-card" />
          <div className="h-40 animate-pulse rounded-3xl border border-border bg-card" />
        </div>
      ) : (
        <div
          className={cn(
            "grid gap-4",
            bento ? "sm:grid-cols-3" : "sm:grid-cols-2 lg:grid-cols-3",
          )}
        >
          {sources.map((source, i) => (
            <SourceTile
              key={source.name}
              source={source}
              variant={variantOf(i, sources.length)}
            />
          ))}
        </div>
      )}
    </section>
  );
}

function SourceTile({ source, variant }: { source: SourcePublic; variant: Variant }) {
  const Icon = kindIcon(source.kind);

  return (
    <Shell variant={variant} hero={variant === "hero"}>
      <Icon
        className={cn(
          "pointer-events-none absolute -z-10 text-primary/[0.05] transition-transform duration-500 group-hover:scale-110",
          variant === "hero" ? "-bottom-10 -right-8 h-56 w-56" : "-bottom-6 -right-6 h-32 w-32",
        )}
      />

      {variant === "wide" ? (
        <div className="flex flex-col gap-4 sm:flex-row sm:items-center">
          <Header source={source} Icon={Icon} />
          <p className="text-sm text-muted-foreground sm:max-w-xs">{source.description}</p>
          <div className="flex items-end gap-8 sm:ml-auto">
            <Stat value={source.prices} label="цен в базе" />
            <Stat value={source.cities} label="городов" />
            <SiteLink href={source.website} />
          </div>
        </div>
      ) : (
        <>
          <Header source={source} Icon={Icon} hero={variant === "hero"} />
          <p
            className={cn(
              "mt-3 flex-1 leading-relaxed text-muted-foreground",
              variant === "hero" ? "text-base" : "text-sm",
            )}
          >
            {source.description}
          </p>
          <div className="mt-5 flex items-end justify-between border-t border-secondary pt-4">
            <Stat value={source.prices} label="цен в базе" size={variant === "hero" ? "xl" : "md"} />
            <Stat value={source.cities} label="городов" />
          </div>
          <SiteLink href={source.website} className="mt-4" />
        </>
      )}
    </Shell>
  );
}

function Shell({
  variant,
  hero,
  children,
}: {
  variant: Variant;
  hero: boolean;
  children: ReactNode;
}) {
  return (
    <article
      onMouseMove={trackSpotlight}
      className={cn(
        "group relative isolate flex flex-col overflow-hidden rounded-3xl border p-6 shadow-sm transition-all duration-300 hover:-translate-y-1 hover:shadow-xl",
        hero
          ? "border-primary/20 bg-gradient-to-br from-accent to-white sm:col-span-2 sm:row-span-2"
          : "border-border bg-white hover:border-primary/40",
        variant === "wide" && "sm:col-span-3",
      )}
    >
      <div
        className="pointer-events-none absolute inset-0 -z-10 opacity-0 transition-opacity duration-300 group-hover:opacity-100"
        style={{
          background:
            "radial-gradient(340px circle at var(--spot-x) var(--spot-y), rgba(217,119,87,0.13), transparent 70%)",
        }}
      />
      {children}
    </article>
  );
}

function Header({
  source,
  Icon,
  hero = false,
}: {
  source: SourcePublic;
  Icon: typeof FlaskConical;
  hero?: boolean;
}) {
  return (
    <div className="flex items-center gap-3.5">
      <span
        className={cn(
          "flex shrink-0 items-center justify-center rounded-2xl bg-accent text-primary ring-1 ring-primary/10 transition-colors group-hover:bg-primary group-hover:text-primary-foreground",
          hero ? "h-14 w-14" : "h-12 w-12",
        )}
      >
        <Icon className={hero ? "h-7 w-7" : "h-6 w-6"} />
      </span>
      <div className="min-w-0">
        <div
          className={cn(
            "truncate font-semibold text-foreground",
            hero ? "text-xl" : "text-lg",
          )}
        >
          {source.display_name}
        </div>
        <span className="text-xs font-medium text-muted-foreground">{source.kind}</span>
      </div>
    </div>
  );
}

function Stat({
  value,
  label,
  size = "md",
}: {
  value: number;
  label: string;
  size?: "md" | "xl";
}) {
  return (
    <div>
      <div
        className={cn(
          "font-bold tracking-tight text-foreground",
          size === "xl" ? "text-4xl" : "text-2xl",
        )}
      >
        {fmt(value)}
      </div>
      <div className="mt-0.5 text-[11px] uppercase tracking-wide text-muted-foreground">
        {label}
      </div>
    </div>
  );
}

function SiteLink({ href, className }: { href: string; className?: string }) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noreferrer"
      className={cn(
        "inline-flex w-fit items-center gap-1 text-sm font-semibold text-primary transition-colors hover:text-primary-hover",
        className,
      )}
    >
      Перейти на сайт <ExternalLink className="h-3.5 w-3.5" />
    </a>
  );
}
