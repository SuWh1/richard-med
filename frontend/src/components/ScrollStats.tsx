import { useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ShieldCheck } from "lucide-react";

import { fetchAnalyticsOverview } from "@/lib/api";
import { ScrollReveal } from "./ScrollReveal";

const prefersReducedMotion = () =>
  typeof window !== "undefined" &&
  window.matchMedia("(prefers-reduced-motion: reduce)").matches;

const easeOutCubic = (t: number) => 1 - Math.pow(1 - t, 3);

interface StatDef {
  value: number;
  label: string;
}

export function ScrollStats() {
  const { data } = useQuery({
    queryKey: ["overview-hero"],
    queryFn: () => fetchAnalyticsOverview({}),
  });
  const ref = useRef<HTMLElement>(null);
  const rafRef = useRef<number | null>(null);
  const [count, setCount] = useState(prefersReducedMotion() ? 1 : 0);

  useEffect(() => {
    if (prefersReducedMotion() || !ref.current) return;
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (!entry.isIntersecting) return;
        observer.disconnect();
        const start = performance.now();
        const tick = (now: number) => {
          const t = Math.min((now - start) / 1200, 1);
          setCount(easeOutCubic(t));
          if (t < 1) rafRef.current = requestAnimationFrame(tick);
        };
        rafRef.current = requestAnimationFrame(tick);
      },
      { threshold: 0.4 },
    );
    observer.observe(ref.current);
    return () => {
      observer.disconnect();
      if (rafRef.current !== null) cancelAnimationFrame(rafRef.current);
    };
  }, [data]);

  if (!data) return null;

  const stats: StatDef[] = [
    { value: data.total_services, label: "услуг в каталоге" },
    { value: data.total_prices, label: "актуальных цен" },
    { value: data.cities.length, label: "городов" },
  ];

  return (
    <section
      ref={ref}
      className="flex flex-col items-center px-4 py-20 text-center sm:py-28"
    >
      <ScrollReveal className="mb-7 text-xs font-semibold uppercase tracking-widest text-faintest sm:mb-10">
        Richard Med в цифрах
      </ScrollReveal>
      <ScrollReveal delay={80} className="grid grid-cols-3 gap-4 sm:gap-16">
        {stats.map((s) => (
          <div key={s.label}>
            <div className="text-4xl font-bold tabular-nums leading-none text-foreground sm:text-7xl">
              {Math.round(s.value * count).toLocaleString("ru-RU")}
            </div>
            <div className="mt-2 text-[10px] uppercase tracking-wide text-muted-foreground sm:mt-3 sm:text-sm">
              {s.label}
            </div>
          </div>
        ))}
      </ScrollReveal>
      <ScrollReveal
        delay={160}
        className="mt-7 inline-flex items-center gap-2 text-sm text-muted-foreground sm:text-base"
      >
        <ShieldCheck className="h-4 w-4 text-primary sm:h-5 sm:w-5" />
        источник у каждой цены
      </ScrollReveal>
    </section>
  );
}
