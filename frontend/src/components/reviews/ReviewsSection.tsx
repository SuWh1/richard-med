import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ExternalLink, MessageSquare, Star } from "lucide-react";

import { fetchClinicReviews } from "@/lib/api";
import { formatRating, formatReviewCount, reviewWord } from "@/lib/rating";
import { Skeleton } from "@/components/ui/skeleton";
import { Pager } from "@/components/Pager";
import { ReviewItem } from "./ReviewItem";

interface ReviewsSectionProps {
  clinicId: number;
  rating: number | null;
  reviewsCount: number;
  sourceHref?: string;
}

const FETCH_LIMIT = 30;
const PER_PAGE = 5;

export function ReviewsSection({
  clinicId,
  rating,
  reviewsCount,
  sourceHref,
}: ReviewsSectionProps) {
  const reviewsQuery = useQuery({
    queryKey: ["clinic-reviews", clinicId],
    queryFn: () => fetchClinicReviews(clinicId, FETCH_LIMIT),
    enabled: rating != null,
  });

  const [page, setPage] = useState(1);
  useEffect(() => setPage(1), [clinicId]);

  if (rating == null) return null;
  const reviews = reviewsQuery.data ?? [];
  const totalPages = Math.ceil(reviews.length / PER_PAGE);
  const pageItems = reviews.slice((page - 1) * PER_PAGE, page * PER_PAGE);

  return (
    <div className="mt-6 overflow-hidden rounded-2xl border border-border bg-white shadow-sm">
      <div className="flex flex-wrap items-center gap-x-4 gap-y-3 border-b border-border px-5 py-4">
        <div className="flex items-center gap-2">
          <MessageSquare className="h-4 w-4 text-muted-foreground" />
          <h2 className="font-semibold text-foreground">Отзывы</h2>
        </div>
        <div className="flex items-center gap-2 rounded-xl bg-secondary px-3 py-1.5">
          <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
          <span className="text-lg font-bold leading-none text-foreground">
            {formatRating(rating)}
          </span>
          <span className="text-xs text-muted-foreground">
            {formatReviewCount(reviewsCount)} {reviewWord(reviewsCount)}
          </span>
        </div>
        {sourceHref ? (
          <a
            href={sourceHref}
            target="_blank"
            rel="noreferrer"
            className="ml-auto inline-flex items-center gap-1 text-[11px] text-muted-foreground transition-colors hover:text-primary"
          >
            Источник: 2ГИС <ExternalLink className="h-3 w-3" />
          </a>
        ) : (
          <span className="ml-auto text-[11px] text-faintest">Источник: 2ГИС</span>
        )}
      </div>

      <div className="px-5">
        {reviewsQuery.isLoading && (
          <div className="space-y-4 py-4">
            {Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className="flex gap-3">
                <Skeleton className="h-7 w-7 rounded-full" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-3 w-32" />
                  <Skeleton className="h-3 w-full" />
                  <Skeleton className="h-3 w-2/3" />
                </div>
              </div>
            ))}
          </div>
        )}

        {reviewsQuery.isError && (
          <p className="py-6 text-sm text-destructive">Не удалось загрузить отзывы.</p>
        )}

        {reviewsQuery.isSuccess && reviews.length === 0 && (
          <p className="py-6 text-sm text-muted-foreground">
            Текстовых отзывов пока нет, но рейтинг основан на {formatReviewCount(reviewsCount)}{" "}
            {reviewWord(reviewsCount)}.
          </p>
        )}

        <div className="divide-y divide-secondary">
          {pageItems.map((review) => (
            <ReviewItem key={review.id} review={review} />
          ))}
        </div>

        {totalPages > 1 && (
          <div className="border-t border-secondary py-3">
            <Pager page={page} totalPages={totalPages} onPage={setPage} />
          </div>
        )}
      </div>
    </div>
  );
}
