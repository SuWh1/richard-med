import { useEffect, useState } from "react";
import { useLocation, useParams, useSearchParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import {
  Check,
  Clock,
  ExternalLink,
  Globe,
  MapPin,
  Navigation,
  Phone,
  Search,
} from "lucide-react";

import { fetchClinic, fetchClinicServices } from "@/lib/api";
import { type SearchContext, searchCrumb } from "@/lib/breadcrumb";
import { capitalize, formatPrice, sourceLabel } from "@/lib/format";
import { type Coords } from "@/lib/geo";
import { geoRouteHandler } from "@/lib/geoRoute";
import { twoGisRouteUrl, twoGisSearchUrl } from "@/lib/twoGisRoute";
import { useUserLocation } from "@/hooks/useUserLocation";
import { useDebounce } from "@/hooks/useDebounce";
import type { BranchInfo, ClinicDetail } from "@/types";
import { ClinicAvatar } from "@/components/ClinicAvatar";
import { StatusBadge } from "@/components/StatusBadge";
import { RatingBadge } from "@/components/RatingBadge";
import { ReviewsSection } from "@/components/reviews/ReviewsSection";
import { AppShell } from "@/components/AppShell";
import { Skeleton } from "@/components/ui/skeleton";
import { ClinicCardSkeletonList } from "@/components/ClinicCardSkeleton";
import { AnimatedList } from "@/components/AnimatedList";
import { ClinicLocationMap } from "@/components/map/ClinicLocationMap";
import { BranchesSection } from "@/components/clinic/BranchesSection";
import { Pager } from "@/components/Pager";

const PAGE_SIZE = 10;

function branchRouteUrl(
  branch: BranchInfo,
  clinic: ClinicDetail,
  origin: Coords | null,
): string {
  if (branch.lat != null && branch.lng != null) {
    return twoGisRouteUrl({
      dest: { lat: branch.lat, lng: branch.lng },
      origin,
      city: branch.city,
    });
  }
  const query = [branch.city, branch.address, clinic.name].filter(Boolean).join(", ");
  return twoGisSearchUrl({ query, city: branch.city });
}

export function ClinicDetailPage() {
  const { id } = useParams();
  const [searchParams, setSearchParams] = useSearchParams();
  const fromSearch = useLocation().state as SearchContext | null;
  const clinicId = Number(id);
  const valid = Number.isInteger(clinicId) && clinicId > 0;
  const [serviceQuery, setServiceQuery] = useState("");
  const { coords, requestOnce } = useUserLocation();

  const clinicQuery = useQuery({
    queryKey: ["clinic", clinicId],
    queryFn: () => fetchClinic(clinicId),
    enabled: valid,
  });
  const debouncedServiceQuery = useDebounce(serviceQuery, 300);
  const [page, setPage] = useState(1);
  useEffect(() => setPage(1), [debouncedServiceQuery]);

  const servicesQuery = useQuery({
    queryKey: ["clinic-services", clinicId, debouncedServiceQuery, page],
    queryFn: () =>
      fetchClinicServices(clinicId, {
        q: debouncedServiceQuery.trim() || undefined,
        limit: PAGE_SIZE,
        offset: (page - 1) * PAGE_SIZE,
      }),
    enabled: valid,
  });

  const clinic = clinicQuery.data;
  const pageItems = servicesQuery.data?.items ?? [];
  const servicesTotal = servicesQuery.data?.total ?? 0;
  const totalPages = Math.max(1, Math.ceil(servicesTotal / PAGE_SIZE));

  const branchParam = Number(searchParams.get("branch"));
  const branch =
    (branchParam ? clinic?.branches.find((b) => b.id === branchParam) : undefined) ??
    clinic?.branches[0];
  const twoGisHref = clinic
    ? twoGisSearchUrl({ query: clinic.name, city: branch?.city })
    : undefined;

  return (
    <AppShell
      breadcrumb={[
        { label: "Поиск", href: "/search" },
        ...searchCrumb(fromSearch),
        { label: clinic?.name ?? "Клиника" },
      ]}
    >
      <div className="mx-auto w-full max-w-[1400px] px-4 py-6 lg:px-6">
        {clinicQuery.isLoading && <ClinicCardSkeletonList count={2} />}
        {clinicQuery.isError && (
          <p className="text-sm text-destructive">Клиника не найдена.</p>
        )}

        {clinic && (
          <>
            <div className="mb-6 rounded-2xl border border-border bg-white p-6 shadow-sm">
              <div className="flex items-start gap-4">
                <ClinicAvatar name={clinic.name} size="lg" />
                <div className="min-w-0 flex-1">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between sm:gap-4">
                    <div className="min-w-0">
                      <h1 className="mb-1 text-xl font-semibold text-foreground sm:text-2xl">
                        {clinic.name}
                      </h1>
                      {clinic.rating != null && (
                        <a
                          href={twoGisHref}
                          target="_blank"
                          rel="noreferrer"
                          title="Смотреть отзывы в 2ГИС"
                          className="mb-1.5 inline-flex items-center gap-1 transition-opacity hover:opacity-80"
                        >
                          <RatingBadge
                            rating={clinic.rating}
                            reviewsCount={clinic.reviews_count}
                            size="md"
                          />
                          <ExternalLink className="h-3 w-3 text-muted-foreground" />
                        </a>
                      )}
                      {branch?.address && (
                        <div className="mb-1 flex items-center gap-1.5 text-sm text-muted-foreground">
                          <MapPin className="h-3.5 w-3.5 shrink-0" />
                          {[branch.city, branch.address].filter(Boolean).join(", ")}
                        </div>
                      )}
                      <div className="flex flex-wrap items-center gap-4 text-sm text-muted-foreground">
                        {branch?.phone && (
                          <span className="flex items-center gap-1">
                            <Phone className="h-3.5 w-3.5" /> {branch.phone}
                          </span>
                        )}
                        {branch?.working_hours && (
                          <span className="flex items-center gap-1">
                            <Clock className="h-3.5 w-3.5" /> {branch.working_hours}
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="order-first flex flex-row items-center gap-2 sm:order-none sm:flex-col sm:items-end">
                      <StatusBadge variant="success">
                        <Check className="h-3 w-3" /> Верифицировано
                      </StatusBadge>
                      <span className="text-xs text-muted-foreground">
                        {sourceLabel(clinic.source_name)}
                      </span>
                    </div>
                  </div>

                  <div className="mt-5 flex flex-wrap gap-3">
                    {branch && (
                      <a
                        href={branchRouteUrl(branch, clinic, coords)}
                        target="_blank"
                        rel="noreferrer"
                        onClick={geoRouteHandler(
                          (c) => branchRouteUrl(branch, clinic, c),
                          coords,
                          requestOnce,
                        )}
                        className="flex min-h-[44px] items-center gap-2 rounded-xl border border-border px-5 py-2.5 text-sm text-muted-foreground transition-colors hover:bg-secondary"
                      >
                        <Navigation className="h-4 w-4" /> Маршрут
                      </a>
                    )}
                    {clinic.website_url && (
                      <a
                        href={clinic.website_url}
                        target="_blank"
                        rel="noreferrer"
                        className="flex min-h-[44px] items-center gap-2 rounded-xl border border-border px-5 py-2.5 text-sm text-muted-foreground transition-colors hover:bg-secondary"
                      >
                        <Globe className="h-4 w-4" /> Сайт клиники
                      </a>
                    )}
                  </div>
                </div>
              </div>
            </div>

            {branch?.lat != null && branch?.lng != null && (
              <div className="mb-6 h-64 overflow-hidden rounded-2xl border border-border shadow-sm sm:h-80">
                <ClinicLocationMap
                  lat={branch.lat}
                  lng={branch.lng}
                  name={clinic.name}
                  address={branch.address}
                  city={branch.city}
                  userCoords={coords}
                  onRequestLocation={requestOnce}
                />
              </div>
            )}

            <BranchesSection
              branches={clinic.branches}
              selectedId={branch?.id}
              userCoords={coords}
              onRequestLocation={requestOnce}
              onSelect={(branchId) =>
                setSearchParams(
                  (prev) => {
                    prev.set("branch", String(branchId));
                    return prev;
                  },
                  { replace: true },
                )
              }
            />

            <div className="overflow-hidden rounded-2xl border border-border bg-white shadow-sm">
              <div className="flex flex-col gap-3 border-b border-border px-5 py-4 sm:flex-row sm:items-center">
                <div className="flex items-center gap-3">
                  <h2 className="whitespace-nowrap font-semibold text-foreground">
                    Все услуги клиники
                  </h2>
                  <span className="rounded-full bg-secondary px-2 py-0.5 text-[11px] text-muted-foreground">
                    {servicesTotal}
                  </span>
                </div>
                <div className="flex items-center gap-2 rounded-lg border border-border bg-input-background px-3 py-1.5 sm:ml-auto">
                  <Search className="h-3.5 w-3.5 shrink-0 text-faintest" />
                  <input
                    value={serviceQuery}
                    onChange={(e) => setServiceQuery(e.target.value)}
                    placeholder="Поиск услуги…"
                    className="w-full bg-transparent text-sm text-foreground outline-none placeholder:text-faintest sm:w-28"
                  />
                </div>
              </div>

              {servicesQuery.isLoading && (
                <div className="divide-y divide-secondary">
                  {Array.from({ length: 6 }).map((_, i) => (
                    <div
                      key={i}
                      className="flex items-center justify-between gap-3 px-5 py-3.5"
                    >
                      <div className="flex-1 space-y-2">
                        <Skeleton className="h-4 w-2/3" />
                        <Skeleton className="h-3 w-24" />
                      </div>
                      <Skeleton className="h-5 w-16" />
                    </div>
                  ))}
                </div>
              )}

              {servicesQuery.isSuccess && pageItems.length === 0 && (
                <p className="px-5 py-6 text-sm text-muted-foreground">
                  {debouncedServiceQuery
                    ? "Ничего не найдено по этому запросу."
                    : "Актуальных цен нет."}
                </p>
              )}

              <AnimatedList className="divide-y divide-secondary">
                {pageItems.map((s) => (
                  <div
                    key={`${s.service_id}-${s.branch_id}`}
                    className="flex items-center gap-3 px-5 py-3.5 transition-colors hover:bg-secondary/50"
                  >
                    <div className="min-w-0 flex-1">
                      <div className="mb-1 truncate text-sm text-foreground">
                        {s.service_name}
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="text-[11px] text-muted-foreground">
                          {capitalize(s.category)}
                        </span>
                      </div>
                    </div>
                    <div className="flex shrink-0 items-center gap-3">
                      <span className="text-base font-bold text-foreground">
                        {formatPrice(s.price_kzt)}
                      </span>
                      <a
                        href={s.source_url}
                        target="_blank"
                        rel="noreferrer"
                        className="flex items-center gap-1 rounded-lg border border-primary/30 px-2.5 py-1 text-[11px] text-primary transition-colors hover:bg-accent/40"
                      >
                        Источник <ExternalLink className="h-3 w-3" />
                      </a>
                    </div>
                  </div>
                ))}
              </AnimatedList>

              {totalPages > 1 && (
                <div className="border-t border-border px-3 py-3">
                  <Pager page={page} totalPages={totalPages} onPage={setPage} />
                </div>
              )}
            </div>

            <ReviewsSection
              clinicId={clinic.id}
              rating={clinic.rating}
              reviewsCount={clinic.reviews_count}
              sourceHref={twoGisHref}
            />
          </>
        )}
      </div>
    </AppShell>
  );
}
