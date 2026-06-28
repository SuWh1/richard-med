import { CornerDownRight } from "lucide-react";

import type { ClinicReview } from "@/types";
import { formatReviewDate } from "@/lib/format";
import { ClinicAvatar } from "@/components/ClinicAvatar";
import { ReviewStars } from "./ReviewStars";

interface ReviewItemProps {
  review: ClinicReview;
}

export function ReviewItem({ review }: ReviewItemProps) {
  const author = review.author?.trim() || "Гость";
  const date = formatReviewDate(review.review_date);

  return (
    <div className="py-4">
      <div className="flex items-start gap-3">
        <ClinicAvatar name={author} size="sm" />
        <div className="min-w-0 flex-1">
          <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
            <span className="text-sm font-medium text-foreground">{author}</span>
            {review.rating != null && <ReviewStars rating={review.rating} />}
            {date && (
              <span className="text-[11px] text-muted-foreground">{date}</span>
            )}
          </div>
          {review.text && (
            <p className="mt-1.5 whitespace-pre-line text-sm leading-relaxed text-foreground/90">
              {review.text}
            </p>
          )}
          {review.official_answer && (
            <div className="mt-3 rounded-lg border-l-2 border-primary/40 bg-secondary/60 px-3 py-2">
              <div className="mb-1 flex items-center gap-1.5 text-[11px] font-medium text-primary">
                <CornerDownRight className="h-3 w-3" /> Ответ клиники
              </div>
              <p className="whitespace-pre-line text-[13px] leading-relaxed text-muted-foreground">
                {review.official_answer}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
