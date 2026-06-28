export function buildCompareHref(
  serviceId: number,
  clinicIds: number[],
  city?: string | null,
): string {
  const params = new URLSearchParams({
    service_id: String(serviceId),
    clinic_ids: clinicIds.join(","),
  });
  if (city) params.set("city", city);
  return `/compare?${params.toString()}`;
}

export function parseClinicIds(raw: string | null): number[] {
  if (!raw) return [];
  return raw
    .split(",")
    .map((s) => Number(s))
    .filter((n) => Number.isInteger(n) && n > 0);
}
