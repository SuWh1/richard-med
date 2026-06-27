import type { PriceCard } from "@/types";
import { formatPrice } from "@/lib/format";

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-0.5 border-b border-slate-100 py-2 last:border-0">
      <dt className="text-xs uppercase tracking-wide text-slate-400">{label}</dt>
      <dd className="text-sm text-slate-800 break-words">{value}</dd>
    </div>
  );
}

export function PricePassport({
  card,
  onClose,
}: {
  card: PriceCard;
  onClose: () => void;
}) {
  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-black/40 p-0 sm:items-center sm:p-4"
      onClick={onClose}
    >
      <div
        className="w-full max-w-lg rounded-t-2xl bg-white p-6 shadow-xl sm:rounded-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between">
          <div>
            <h2 className="text-lg font-semibold text-slate-900">Паспорт цены</h2>
            <p className="text-sm text-slate-500">{card.clinic_name}</p>
          </div>
          <button
            onClick={onClose}
            className="rounded-full p-1 text-slate-400 hover:bg-slate-100"
            aria-label="Закрыть"
          >
            ✕
          </button>
        </div>

        <dl>
          <Row label="Цена" value={formatPrice(card.price_kzt)} />
          <Row label="Услуга (нормализовано)" value={card.service_name} />
          <Row
            label="Исходное название источника"
            value={card.service_name_raw ?? "—"}
          />
          <Row
            label="Уверенность сопоставления"
            value={`${Math.round(card.match_confidence * 100)}% (${card.match_method ?? "—"})`}
          />
          <Row
            label="Дата получения"
            value={new Date(card.parsed_at).toLocaleString("ru-RU")}
          />
          <Row label="Возраст данных" value={`${card.age_days} дн.`} />
          <Row
            label="Источник"
            value={
              <a
                href={card.source_url}
                target="_blank"
                rel="noreferrer"
                className="text-sky-600 underline"
              >
                {card.source_url}
              </a>
            }
          />
          <Row
            label="Контрольная сумма документа"
            value={
              <span className="font-mono text-xs">
                {card.content_hash ? `${card.content_hash.slice(0, 16)}…` : "—"}
              </span>
            }
          />
        </dl>
      </div>
    </div>
  );
}
