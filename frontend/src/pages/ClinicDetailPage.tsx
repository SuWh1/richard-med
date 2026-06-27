import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Globe, MapPin, Phone } from "lucide-react";

import { fetchClinic, fetchClinicServices } from "@/lib/api";
import { formatPrice } from "@/lib/format";
import { ClinicAvatar } from "@/components/ClinicAvatar";
import { FreshBadge } from "@/components/FreshBadge";

export function ClinicDetailPage() {
  const { id } = useParams();
  const clinicId = Number(id);
  const valid = Number.isInteger(clinicId) && clinicId > 0;

  const clinicQuery = useQuery({
    queryKey: ["clinic", clinicId],
    queryFn: () => fetchClinic(clinicId),
    enabled: valid,
  });
  const servicesQuery = useQuery({
    queryKey: ["clinic-services", clinicId],
    queryFn: () => fetchClinicServices(clinicId),
    enabled: valid,
  });

  const clinic = clinicQuery.data;
  const services = servicesQuery.data ?? [];

  return (
    <div className="mx-auto max-w-3xl px-4 py-8">
      <Link to="/" className="text-sm font-medium text-primary hover:underline">
        ← К поиску
      </Link>

      {clinicQuery.isLoading && (
        <p className="mt-6 text-sm text-muted-foreground">Загрузка…</p>
      )}
      {clinicQuery.isError && (
        <p className="mt-6 text-sm text-destructive">Клиника не найдена.</p>
      )}

      {clinic && (
        <>
          <header className="mt-4 flex items-start gap-4">
            <ClinicAvatar name={clinic.name} size="lg" />
            <div className="min-w-0">
              <h1 className="text-xl font-semibold text-foreground">{clinic.name}</h1>
              {clinic.website_url && (
                <a
                  href={clinic.website_url}
                  target="_blank"
                  rel="noreferrer"
                  className="mt-1 inline-flex items-center gap-1 text-sm text-primary hover:underline"
                >
                  <Globe className="h-3.5 w-3.5" /> {clinic.website_url}
                </a>
              )}
            </div>
          </header>

          <section className="mt-6 grid gap-3 sm:grid-cols-2">
            {clinic.branches.map((b) => (
              <div key={b.id} className="rounded-xl border border-border bg-white p-4 shadow-sm">
                <div className="flex items-center gap-1.5 text-sm font-medium text-foreground">
                  <MapPin className="h-3.5 w-3.5 text-primary" /> {b.city}
                </div>
                {b.address && (
                  <div className="mt-0.5 text-sm text-muted-foreground">{b.address}</div>
                )}
                {b.phone && (
                  <div className="mt-1 flex items-center gap-1.5 text-xs text-muted-foreground">
                    <Phone className="h-3 w-3" /> {b.phone}
                  </div>
                )}
                {b.working_hours && (
                  <div className="mt-0.5 text-xs text-muted-foreground">{b.working_hours}</div>
                )}
              </div>
            ))}
          </section>

          <section className="mt-8">
            <h2 className="mb-3 font-semibold text-foreground">Все услуги клиники</h2>
            {servicesQuery.isSuccess && services.length === 0 && (
              <p className="text-sm text-muted-foreground">Актуальных цен нет.</p>
            )}
            <div className="divide-y divide-secondary rounded-xl border border-border bg-white">
              {services.map((s) => (
                <div
                  key={`${s.service_id}-${s.branch_id}`}
                  className="flex items-center justify-between gap-3 px-4 py-3"
                >
                  <div className="min-w-0">
                    <div className="truncate text-sm font-medium text-foreground">
                      {s.service_name}
                    </div>
                    <div className="text-xs text-muted-foreground">{s.category}</div>
                  </div>
                  <div className="flex shrink-0 items-center gap-3">
                    <FreshBadge freshness={s.freshness} ageDays={s.age_days} />
                    <span className="font-semibold text-foreground">
                      {formatPrice(s.price_kzt)}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </>
      )}
    </div>
  );
}
