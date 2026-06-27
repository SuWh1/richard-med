export function buildCompareHref(serviceId: number, clinicIds: number[]): string {
  const params = new URLSearchParams({
    service_id: String(serviceId),
    clinic_ids: clinicIds.join(","),
  });
  return `/compare?${params.toString()}`;
}

export function parseClinicIds(raw: string | null): number[] {
  if (!raw) return [];
  return raw
    .split(",")
    .map((s) => Number(s))
    .filter((n) => Number.isInteger(n) && n > 0);
}
