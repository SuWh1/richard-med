import type { ReactNode } from "react";
import { Clock, MapPin, Shield } from "lucide-react";

import type { City } from "@/types";
import { POPULAR_SERVICES } from "@/lib/constants";

const TRUST = [
  { Icon: Shield, title: "Источник каждой цены", desc: "Ссылка на прайс-лист клиники" },
  { Icon: Clock, title: "Свежесть до 30 дней", desc: "Автоматическое обновление данных" },
  { Icon: MapPin, title: "Сравнение и карта", desc: "Маршрут от вашей точки" },
];

interface HomeHeroProps {
  city: City;
  searchBar: ReactNode;
  onPickPopular: (query: string) => void;
}

export function HomeHero({ city, searchBar, onPickPopular }: HomeHeroProps) {
  return (
    <main className="flex flex-1 flex-col items-center justify-center px-4 py-16">
      <div className="mb-7 inline-flex items-center gap-2 rounded-full bg-accent px-4 py-1.5 text-sm font-medium text-primary">
        <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-primary" />
        Казахстан · {city}
      </div>

      <h1 className="mb-4 max-w-xl text-center text-[40px] font-semibold leading-[1.2] text-foreground">
        Сравните цены на <span className="text-primary">медицинские</span>
        <br />
        услуги в Казахстане
      </h1>
      <p className="mb-9 max-w-lg text-center text-lg leading-relaxed text-muted-foreground">
        Один поиск — реальные цены клиник, источник, свежесть и маршрут.
      </p>

      <div className="mb-10 w-full max-w-xl">{searchBar}</div>

      <div className="mb-10 grid w-full max-w-xl grid-cols-1 gap-4 sm:grid-cols-3">
        {TRUST.map(({ Icon, title, desc }) => (
          <div
            key={title}
            className="rounded-xl border border-border bg-white p-4 text-center shadow-sm"
          >
            <div className="mx-auto mb-2.5 flex h-9 w-9 items-center justify-center rounded-xl bg-accent">
              <Icon className="h-5 w-5 text-primary" />
            </div>
            <div className="mb-1 text-xs font-semibold text-foreground">{title}</div>
            <div className="text-[11px] text-muted-foreground">{desc}</div>
          </div>
        ))}
      </div>

      <div className="flex flex-col items-center gap-3">
        <div className="text-[11px] font-semibold uppercase tracking-widest text-[#CBD5E1]">
          Популярные услуги
        </div>
        <div className="flex flex-wrap justify-center gap-2">
          {POPULAR_SERVICES.map((s) => (
            <button
              key={s}
              type="button"
              onClick={() => onPickPopular(s)}
              className="min-h-[40px] rounded-full border border-border bg-white px-4 py-2 text-sm text-muted-foreground shadow-sm transition-all hover:border-primary/50 hover:bg-accent/30 hover:text-primary"
            >
              {s}
            </button>
          ))}
        </div>
      </div>
    </main>
  );
}
