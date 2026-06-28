import { Star } from "lucide-react";

import { cn } from "@/components/ui/utils";
import { formatRating, formatReviewCount } from "@/lib/rating";

interface RatingBadgeProps {
  rating: number | null;
  reviewsCount?: number | null;
  size?: "sm" | "md";
  className?: string;
}

export function RatingBadge({
  rating,
  reviewsCount,
  size = "sm",
  className,
}: RatingBadgeProps) {
  if (rating == null) return null;
  const sm = size === "sm";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 font-semibold text-foreground",
        sm ? "text-[11px]" : "text-sm",
        className,
      )}
      aria-label={`Рейтинг 2ГИС ${formatRating(rating)}`}
    >
      <Star
        className={cn(
          "fill-amber-400 text-amber-400",
          sm ? "h-3 w-3" : "h-3.5 w-3.5",
        )}
      />
      {formatRating(rating)}
      {reviewsCount != null && reviewsCount > 0 && (
        <span className="font-normal text-muted-foreground">
          · {formatReviewCount(reviewsCount)}
        </span>
      )}
    </span>
  );
}
