import { useQuery } from "@tanstack/react-query";

import { fetchFeatured } from "@/lib/api";
import { formatPrice } from "@/lib/format";
import { useCountUp } from "@/hooks/useCountUp";
import { ClinicAvatar } from "./ClinicAvatar";
import { ScrollReveal } from "./ScrollReveal";
import { GlowCard } from "./GlowCard";

function CountUpPrice({ value }: { value: number }) {
  const animated = useCountUp(value);
  return <>{formatPrice(animated)}</>;
}

interface FeaturedPricesProps {
  onPick: (serviceName: string) => void;
}

export function FeaturedPrices({ onPick }: FeaturedPricesProps) {
  const { data } = useQuery({
    queryKey: ["featured"],
    queryFn: () => fetchFeatured(4),
  });

  const cards = data ?? [];
  if (cards.length === 0) return null;

  return (
    <div className="mt-12 w-full max-w-3xl">
      <ScrollReveal>
        <div className="mb-3 text-center text-[11px] font-semibold uppercase tracking-widest text-faintest">
          Актуальные цены прямо сейчас
        </div>
      </ScrollReveal>
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
        {cards.map((card, i) => (
          <ScrollReveal key={card.price_id} delay={i * 80}>
            <GlowCard>
              <button
                type="button"
                onClick={() => onPick(card.service_name)}
                className="flex w-full items-center gap-3 p-3.5 text-left"
              >
                <ClinicAvatar name={card.clinic_name} size="sm" />
              <div className="min-w-0 flex-1">
                <div className="truncate text-sm font-medium text-foreground">
                  {card.service_name}
                </div>
                <div className="mt-0.5 flex items-center gap-2">
                  <span className="truncate text-[11px] text-muted-foreground">
                    {card.clinic_name}
                  </span>
                </div>
              </div>
              <div className="shrink-0 text-base font-bold tabular-nums text-foreground">
                <CountUpPrice value={card.price_kzt} />
              </div>
            </button>
            </GlowCard>
          </ScrollReveal>
        ))}
      </div>
    </div>
  );
}
