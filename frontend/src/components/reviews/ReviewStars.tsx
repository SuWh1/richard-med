import { Star } from "lucide-react";

import { cn } from "@/components/ui/utils";

interface ReviewStarsProps {
  rating: number;
  className?: string;
}

export function ReviewStars({ rating, className }: ReviewStarsProps) {
  const rounded = Math.round(rating);
  return (
    <span
      className={cn("inline-flex items-center gap-0.5", className)}
      aria-label={`Оценка ${rounded} из 5`}
    >
      {Array.from({ length: 5 }).map((_, i) => (
        <Star
          key={i}
          className={cn(
            "h-3.5 w-3.5",
            i < rounded
              ? "fill-amber-400 text-amber-400"
              : "fill-transparent text-border",
          )}
        />
      ))}
    </span>
  );
}
