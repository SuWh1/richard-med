import type { MapPin, PriceCard } from "@/types";

export function medianPrice(prices: number[]): number | null {
  if (prices.length === 0) return null;
  const sorted = [...prices].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 0 ? (sorted[mid - 1] + sorted[mid]) / 2 : sorted[mid];
}

export function savingsVsMedian(price: number, median: number): number {
  return median - price;
}

export function discountPct(price: number, median: number | null): number {
  if (!median) return 0;
  return Math.round(((price - median) / median) * 100);
}

function locationKey(pin: MapPin): string {
  return `${pin.clinic_id}:${pin.lat.toFixed(5)}:${pin.lng.toFixed(5)}`;
}

export function dedupePinsByLocation(pins: MapPin[]): MapPin[] {
  const cheapestAt = new Map<string, MapPin>();
  for (const p of pins) {
    const key = locationKey(p);
    const current = cheapestAt.get(key);
    if (current === undefined || p.price_kzt < current.price_kzt) {
      cheapestAt.set(key, p);
    }
  }
  const order: string[] = [];
  const seen = new Set<string>();
  for (const p of pins) {
    const key = locationKey(p);
    if (!seen.has(key)) {
      seen.add(key);
      order.push(key);
    }
  }
  return order.map((key) => cheapestAt.get(key) as MapPin);
}

export function topCheapestClinicIds(cards: PriceCard[], n: number): number[] {
  const cheapestByClinic = new Map<number, number>();
  for (const c of cards) {
    const current = cheapestByClinic.get(c.clinic_id);
    if (current === undefined || c.price_kzt < current) {
      cheapestByClinic.set(c.clinic_id, c.price_kzt);
    }
  }
  return [...cheapestByClinic.entries()]
    .sort((a, b) => a[1] - b[1])
    .slice(0, n)
    .map(([clinicId]) => clinicId);
}
