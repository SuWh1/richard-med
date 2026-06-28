import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Clock, MapPin, Shield } from "lucide-react";

import type { Suggestion } from "@/types";
import { fetchCities, fetchSuggestions } from "@/lib/api";
import { POPULAR_SERVICES } from "@/lib/constants";
import { geoCityFor } from "@/lib/geo";
import { DEFAULT_CITY, searchHref } from "@/hooks/useSearchState";
import { useDebounce } from "@/hooks/useDebounce";
import { useUserLocation } from "@/hooks/useUserLocation";
import { useAuth } from "@/lib/useAuth";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { CardNav, type CardNavItem } from "@/components/CardNav";
import { SearchBar } from "@/components/SearchBar";
import { TextType } from "@/components/TextType";
import { Reveal } from "@/components/Reveal";
import { ScrollStack, ScrollStackItem } from "@/components/ui/ScrollStack";
import { ScrollStats } from "@/components/ScrollStats";
import { FeaturedPrices } from "@/components/FeaturedPrices";
import { SourcesSection } from "@/components/SourcesSection";
import { Footer } from "@/components/Footer";

const TRUST = [
  { Icon: Shield, title: "Цена с сайта клиники", desc: "Можно проверить по ссылке" },
  { Icon: Clock, title: "Обновляем каждый день", desc: "Цены всегда свежие" },
  { Icon: MapPin, title: "Сравнение и маршрут", desc: "Клиники на карте рядом" },
];

function buildNavItems({
  isAuthenticated,
  isAdmin,
}: {
  isAuthenticated: boolean;
  isAdmin: boolean;
}): CardNavItem[] {
  const cabinetLinks = [
    isAuthenticated
      ? { label: "Личный кабинет", href: "/cabinet" }
      : { label: "Войти", href: "/login" },
  ];
  if (isAdmin) cabinetLinks.push({ label: "Source Health", href: "/dashboard" });

  return [
    {
      label: "Сервис",
      bgColor: "var(--accent)",
      textColor: "var(--primary)",
      links: [
        { label: "Найти услугу", href: "#hero" },
        { label: "Аналитика цен", href: "/analytics" },
      ],
    },
    {
      label: "Кабинет",
      bgColor: "var(--secondary)",
      textColor: "var(--foreground)",
      links: cabinetLinks,
    },
    {
      label: "О проекте",
      bgColor: "var(--primary)",
      textColor: "var(--primary-foreground)",
      dark: true,
      links: [
        { label: "Как это работает", href: "#how" },
        { label: "Источники данных", href: "#sources" },
      ],
    },
  ];
}

export function LandingPage() {
  const navigate = useNavigate();
  const { isAuthenticated, isAdmin } = useAuth();
  const navItems = useMemo(
    () => buildNavItems({ isAuthenticated, isAdmin }),
    [isAuthenticated, isAdmin],
  );
  const [city, setCity] = useState(DEFAULT_CITY);
  const [input, setInput] = useState("");
  const debounced = useDebounce(input, 250);

  const citiesQuery = useQuery({ queryKey: ["cities"], queryFn: fetchCities });
  const cities = citiesQuery.data ?? [];
  const cityNames = cities.length ? cities.map((c) => c.name) : ["Астана", "Алматы"];

  const { coords } = useUserLocation();
  const cityTouched = useRef(false);
  const pickCity = (next: string) => {
    cityTouched.current = true;
    setCity(next);
  };

  useEffect(() => {
    if (cityTouched.current) return;
    const near = geoCityFor(coords, cities, city);
    if (near) setCity(near);
  }, [coords, cities, city]);

  const suggestionsQuery = useQuery({
    queryKey: ["suggestions", debounced],
    queryFn: () => fetchSuggestions(debounced),
    enabled: debounced.trim().length >= 2,
  });

  const go = (q: string) => {
    if (q.trim().length >= 2) navigate(searchHref({ q: q.trim(), city }));
  };

  const cityControl = (
    <Select value={city} onValueChange={pickCity}>
      <SelectTrigger
        size="sm"
        className="h-8 w-auto max-w-[160px] gap-1 rounded-full border-transparent bg-secondary/60 px-2.5 text-muted-foreground hover:bg-secondary [&>span]:truncate"
      >
        <MapPin className="h-3.5 w-3.5 shrink-0 text-primary" />
        <SelectValue />
      </SelectTrigger>
      <SelectContent align="end" className="max-h-72">
        {cityNames.map((c) => (
          <SelectItem key={c} value={c}>
            {c}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  );

  return (
    <div className="flex min-h-screen flex-col bg-background">
      <CardNav items={navItems} cityControl={cityControl} />

      {/* Hero — fluid content that fills the first screen so stats stay below the fold */}
      <section
        id="hero"
        className="relative isolate flex min-h-svh flex-col overflow-hidden bg-background"
      >
        <div className="relative z-20 mx-auto flex w-full max-w-4xl flex-1 flex-col items-center justify-center gap-[clamp(1.25rem,4vh,2.75rem)] px-4 py-8 text-center">
          <Reveal>
            <h1 className="flex min-h-[2.3em] max-w-[26ch] items-start justify-center text-balance font-semibold leading-[1.1] tracking-tight text-foreground text-[clamp(2.1rem,5.4vw,4.5rem)]">
              <TextType
                as="span"
                text={[
                  "Цены на медуслуги в одном месте",
                  "Честные цены клиник рядом",
                  "Сравните и сэкономьте",
                ]}
                highlightWords={["медуслуги", "Честные", "сэкономьте"]}
                highlightClassName="text-primary"
                typingSpeed={55}
                deletingSpeed={32}
                pauseDuration={3600}
                cursorCharacter="|"
                cursorClassName="font-normal text-primary"
              />
            </h1>
            <p className="mx-auto mt-[clamp(0.75rem,2vh,1.5rem)] max-w-xl leading-relaxed text-muted-foreground text-[clamp(1rem,1.6vw,1.375rem)]">
              Один поиск показывает реальные цены клиник, источник, свежесть и маршрут.
            </p>
          </Reveal>

          <Reveal delay={150} className="relative z-30 w-full max-w-xl">
            <SearchBar
              value={input}
              onChange={setInput}
              onSubmit={() => go(input)}
              suggestions={suggestionsQuery.data ?? []}
              onPick={(s: Suggestion) => go(s.name_ru)}
            />
          </Reveal>

          <Reveal delay={230}>
            <div className="flex flex-wrap justify-center gap-2">
              {POPULAR_SERVICES.map((s) => (
                <button
                  key={s}
                  type="button"
                  onClick={() => go(s)}
                  className="min-h-[36px] rounded-full border border-border bg-card/70 px-4 py-1.5 text-sm text-muted-foreground backdrop-blur-sm transition-all hover:-translate-y-0.5 hover:border-primary/50 hover:bg-accent/40 hover:text-primary"
                >
                  {s}
                </button>
              ))}
            </div>
          </Reveal>
        </div>
      </section>

      <ScrollStats />

      {/* Light body */}
      <main className="flex-1 pb-20">
        <section id="how" className="mx-auto w-full max-w-3xl px-4 scroll-mt-24">
          <ScrollStack useWindowScroll rotationAmount={0.6} blurAmount={1.2}>
            {TRUST.map(({ Icon, title, desc }) => (
              <ScrollStackItem key={title}>
                <span className="flex h-16 w-16 items-center justify-center rounded-2xl bg-accent">
                  <Icon className="h-8 w-8 text-primary" />
                </span>
                <div className="mt-6 text-3xl font-semibold tracking-tight text-foreground">
                  {title}
                </div>
                <div className="mt-2 text-lg text-muted-foreground">{desc}</div>
              </ScrollStackItem>
            ))}
          </ScrollStack>
        </section>

        <SourcesSection />

        <div id="prices" className="mx-auto w-full max-w-3xl px-4 scroll-mt-24">
          <FeaturedPrices onPick={go} />
        </div>
      </main>

      <Footer />
    </div>
  );
}
