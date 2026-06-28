import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { Briefcase, MessageSquare, Star } from "lucide-react";

import type { DoctorDetailItem } from "@/types";
import { fetchDoctor, fetchDoctorReviews } from "@/lib/api";
import { formatPrice } from "@/lib/format";
import { AppShell } from "@/components/AppShell";
import { ClinicCardSkeletonList } from "@/components/ClinicCardSkeleton";
import { Skeleton } from "@/components/ui/skeleton";

const REVIEWS_PAGE = 10;

function experienceLabel(years: number): string {
  const mod10 = years % 10;
  const mod100 = years % 100;
  if (mod10 === 1 && mod100 !== 11) return `${years} год`;
  if (mod10 >= 2 && mod10 <= 4 && (mod100 < 10 || mod100 >= 20)) return `${years} года`;
  return `${years} лет`;
}

function groupDetails(details: DoctorDetailItem[]): [string, DoctorDetailItem[]][] {
  const order: string[] = [];
  const map = new Map<string, DoctorDetailItem[]>();
  for (const d of details) {
    if (!map.has(d.detail_type)) {
      map.set(d.detail_type, []);
      order.push(d.detail_type);
    }
    map.get(d.detail_type)!.push(d);
  }
  return order.map((t) => [t, map.get(t)!]);
}

export function DoctorPage() {
  const { id } = useParams();
  const doctorId = Number(id);
  const valid = Number.isInteger(doctorId) && doctorId > 0;
  const [reviewCount, setReviewCount] = useState(REVIEWS_PAGE);

  const profileQuery = useQuery({
    queryKey: ["doctor", doctorId],
    queryFn: () => fetchDoctor(doctorId),
    enabled: valid,
  });
  const reviewsQuery = useQuery({
    queryKey: ["doctor-reviews", doctorId, reviewCount],
    queryFn: () => fetchDoctorReviews(doctorId, reviewCount),
    enabled: valid,
  });

  const doctor = profileQuery.data;
  const grouped = useMemo(() => groupDetails(doctor?.details ?? []), [doctor]);
  const reviews = reviewsQuery.data;

  return (
    <AppShell
      breadcrumb={[
        { label: "Поиск", href: "/" },
        { label: doctor?.name ?? "Врач" },
      ]}
    >
      <div className="mx-auto max-w-4xl px-4 py-6 lg:px-6">
        {profileQuery.isLoading && <ClinicCardSkeletonList count={2} />}
        {profileQuery.isError && (
          <p className="text-sm text-destructive">Врач не найден.</p>
        )}

        {doctor && (
          <>
            <div className="mb-6 rounded-2xl border border-border bg-white p-6 shadow-sm">
              <div className="flex items-start gap-4">
                {doctor.avatar_url ? (
                  <img
                    src={doctor.avatar_url}
                    alt={doctor.name}
                    className="h-20 w-20 shrink-0 rounded-2xl object-cover"
                  />
                ) : (
                  <div className="flex h-20 w-20 shrink-0 items-center justify-center rounded-2xl bg-primary/10 text-2xl font-semibold text-primary">
                    {doctor.name[0]}
                  </div>
                )}
                <div className="min-w-0 flex-1">
                  <h1 className="mb-1 text-2xl font-semibold text-foreground">
                    {doctor.name}
                  </h1>
                  <div className="flex flex-wrap items-center gap-x-4 gap-y-1 text-sm text-muted-foreground">
                    {doctor.rating != null && (
                      <span className="flex items-center gap-1 font-medium text-foreground">
                        <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
                        {doctor.rating.toFixed(1)}
                        {doctor.review_count ? (
                          <span className="font-normal text-muted-foreground">
                            {" "}
                            · {doctor.review_count} отзывов
                          </span>
                        ) : null}
                      </span>
                    )}
                    {doctor.experience_years != null && (
                      <span className="flex items-center gap-1">
                        <Briefcase className="h-4 w-4" /> Стаж{" "}
                        {experienceLabel(doctor.experience_years)}
                      </span>
                    )}
                    {doctor.gender && <span>{doctor.gender}</span>}
                  </div>
                </div>
              </div>

              {doctor.photos && doctor.photos.length > 0 && (
                <div className="mt-5 flex gap-2 overflow-x-auto pb-1">
                  {doctor.photos.slice(0, 6).map((p) => (
                    <img
                      key={p}
                      src={p}
                      alt=""
                      loading="lazy"
                      className="h-24 w-24 shrink-0 rounded-xl object-cover"
                    />
                  ))}
                </div>
              )}
            </div>

            {doctor.prices.length > 0 && (
              <section className="mb-6 overflow-hidden rounded-2xl border border-border bg-white shadow-sm">
                <h2 className="border-b border-border px-5 py-4 font-semibold text-foreground">
                  Услуги и цены
                </h2>
                <div className="divide-y divide-secondary">
                  {doctor.prices.map((p) => (
                    <Link
                      key={p.price_id}
                      to={`/search?q=${encodeURIComponent(p.service_name)}`}
                      className="flex items-center justify-between gap-3 px-5 py-3.5 transition-colors hover:bg-secondary/50"
                    >
                      <div className="min-w-0">
                        <div className="truncate text-sm text-foreground">
                          {p.service_name}
                        </div>
                        <div className="truncate text-[11px] text-muted-foreground">
                          {p.clinic_name}
                        </div>
                      </div>
                      <span className="shrink-0 text-base font-bold text-foreground">
                        {formatPrice(p.price_kzt)}
                      </span>
                    </Link>
                  ))}
                </div>
              </section>
            )}

            {grouped.length > 0 && (
              <section className="mb-6 rounded-2xl border border-border bg-white p-6 shadow-sm">
                <h2 className="mb-4 font-semibold text-foreground">О враче</h2>
                <div className="space-y-5">
                  {grouped.map(([type, items]) => (
                    <div key={type}>
                      <h3 className="mb-2 text-sm font-medium text-muted-foreground">
                        {type}
                      </h3>
                      <ul className="space-y-1.5">
                        {items.map((d, i) => (
                          <li key={i} className="flex gap-2 text-sm text-foreground">
                            <span className="mt-1.5 h-1 w-1 shrink-0 rounded-full bg-primary" />
                            <span>
                              {d.info}
                              {d.year && (
                                <span className="text-muted-foreground"> · {d.year}</span>
                              )}
                            </span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </section>
            )}

            <section className="rounded-2xl border border-border bg-white p-6 shadow-sm">
              <div className="mb-4 flex items-center gap-2">
                <MessageSquare className="h-4 w-4 text-muted-foreground" />
                <h2 className="font-semibold text-foreground">Отзывы</h2>
                {reviews && (
                  <span className="rounded-full bg-secondary px-2 py-0.5 text-[11px] text-muted-foreground">
                    {reviews.total}
                  </span>
                )}
              </div>

              {reviewsQuery.isLoading && (
                <div className="space-y-3">
                  {Array.from({ length: 3 }).map((_, i) => (
                    <Skeleton key={i} className="h-20 w-full" />
                  ))}
                </div>
              )}

              {reviews && reviews.total === 0 && (
                <p className="text-sm text-muted-foreground">Отзывов пока нет.</p>
              )}

              <div className="space-y-3">
                {reviews?.items.map((r) => (
                  <div key={r.id} className="rounded-xl border border-border p-4">
                    <div className="mb-1.5 flex items-center gap-2">
                      {r.score != null && (
                        <span className="flex items-center gap-0.5 text-sm font-semibold text-foreground">
                          <Star className="h-3.5 w-3.5 fill-amber-400 text-amber-400" />
                          {r.score.toFixed(0)}/10
                        </span>
                      )}
                      <span className="text-sm text-foreground">
                        {r.client_name ?? "Аноним"}
                      </span>
                      {r.service_name && (
                        <span className="text-[11px] text-muted-foreground">
                          · {r.service_name}
                        </span>
                      )}
                    </div>
                    {(r.text_ru || r.text) && (
                      <p className="text-sm text-muted-foreground">
                        {r.text_ru || r.text}
                      </p>
                    )}
                    {r.clinic_reply && (
                      <div className="mt-2 rounded-lg bg-secondary/50 p-2.5 text-[12px] text-muted-foreground">
                        <span className="font-medium text-foreground">
                          Ответ клиники:
                        </span>{" "}
                        {r.clinic_reply}
                      </div>
                    )}
                  </div>
                ))}
              </div>

              {reviews && reviews.items.length < reviews.total && (
                <button
                  type="button"
                  onClick={() => setReviewCount((c) => c + REVIEWS_PAGE)}
                  className="mt-4 w-full rounded-xl border border-border py-2.5 text-sm text-muted-foreground transition-colors hover:bg-secondary"
                >
                  Показать ещё
                </button>
              )}
            </section>
          </>
        )}
      </div>
    </AppShell>
  );
}
