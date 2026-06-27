import type { ReactNode } from "react";
import { ExternalLink, Shield } from "lucide-react";

import type { PriceCard } from "@/types";
import { formatPrice, freshnessLabel } from "@/lib/format";
import { cn } from "@/components/ui/utils";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface PricePassportProps {
  card: PriceCard | null;
  onClose: () => void;
}

function Row({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: ReactNode;
  tone?: "default" | "muted" | "price";
}) {
  return (
    <div className="flex items-center justify-between border-b border-secondary py-3 last:border-0">
      <span className="text-sm text-muted-foreground">{label}</span>
      <span
        className={cn(
          "text-sm font-medium",
          tone === "price" && "text-lg font-bold text-primary",
          tone === "muted" && "text-muted-foreground",
          tone === "default" && "text-foreground",
        )}
      >
        {value}
      </span>
    </div>
  );
}

export function PricePassport({ card, onClose }: PricePassportProps) {
  return (
    <Dialog open={card !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-[440px] p-0">
        {card && (
          <>
            <DialogHeader className="flex-row items-center gap-3 space-y-0 border-b border-border px-6 py-4">
              <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-accent">
                <Shield className="h-4 w-4 text-primary" />
              </span>
              <div className="text-left">
                <DialogTitle className="text-base">Паспорт цены</DialogTitle>
                <p className="text-xs text-muted-foreground">Верифицированный источник</p>
              </div>
            </DialogHeader>

            <div className="px-6">
              <Row label="Клиника" value={card.clinic_name} />
              <Row label="Услуга (нормализовано)" value={card.service_name} />
              {card.service_name_raw && (
                <Row label="Исходное название" value={card.service_name_raw} tone="muted" />
              )}
              <Row label="Цена" value={formatPrice(card.price_kzt)} tone="price" />
              <Row
                label="Обновлено"
                value={freshnessLabel(card.freshness, card.age_days)}
              />
              <div className="flex items-center justify-between border-b border-secondary py-3">
                <span className="text-sm text-muted-foreground">
                  Уверенность сопоставления
                </span>
                <span className="flex items-center gap-2">
                  <span className="h-1.5 w-20 overflow-hidden rounded-full bg-border">
                    <span
                      className="block h-full rounded-full bg-primary"
                      style={{ width: `${Math.round(card.match_confidence * 100)}%` }}
                    />
                  </span>
                  <span className="text-sm font-semibold text-foreground">
                    {card.match_confidence.toFixed(2)}
                  </span>
                </span>
              </div>
            </div>

            {card.content_hash && (
              <div className="px-6 py-3">
                <div className="mb-1.5 text-[11px] font-medium uppercase tracking-wide text-muted-foreground">
                  Content Hash
                </div>
                <code className="block truncate rounded-lg border border-border bg-background px-3 py-2 font-mono text-[11px] text-muted-foreground">
                  {card.content_hash.slice(0, 40)}…
                </code>
              </div>
            )}

            <p className="mx-6 mb-4 rounded-xl border border-border bg-background px-4 py-2.5 text-[11px] text-muted-foreground">
              Цена из открытого источника, может измениться. Проверяйте актуальность перед
              записью.
            </p>

            <div className="flex gap-3 px-6 pb-6">
              <a
                href={card.source_url}
                target="_blank"
                rel="noreferrer"
                className="flex flex-1 items-center justify-center gap-1.5 rounded-xl bg-primary py-2.5 text-sm font-medium text-primary-foreground transition-colors hover:bg-[#0b8a7a]"
              >
                <ExternalLink className="h-4 w-4" /> Открыть источник
              </a>
              <button
                type="button"
                onClick={onClose}
                className="flex-1 rounded-xl border border-border py-2.5 text-sm text-muted-foreground transition-colors hover:bg-secondary"
              >
                Закрыть
              </button>
            </div>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
}
