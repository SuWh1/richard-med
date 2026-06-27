import { Skeleton } from "@/components/ui/skeleton";

export function ClinicCardSkeleton() {
  return (
    <div className="rounded-xl border border-border bg-white p-5 shadow-sm">
      <div className="flex items-start gap-3">
        <Skeleton className="h-9 w-9 rounded-full" />
        <div className="flex-1 space-y-2">
          <div className="flex items-start justify-between gap-2">
            <div className="space-y-2">
              <Skeleton className="h-4 w-40" />
              <Skeleton className="h-3 w-28" />
            </div>
            <Skeleton className="h-7 w-24 rounded-lg" />
          </div>
          <Skeleton className="h-3 w-3/4" />
          <div className="flex gap-2 pt-1">
            <Skeleton className="h-8 w-28 rounded-lg" />
            <Skeleton className="h-8 w-20 rounded-lg" />
            <Skeleton className="h-8 w-20 rounded-lg" />
          </div>
        </div>
      </div>
    </div>
  );
}

export function ClinicCardSkeletonList({ count = 4 }: { count?: number }) {
  return (
    <div className="space-y-3">
      {Array.from({ length: count }).map((_, i) => (
        <ClinicCardSkeleton key={i} />
      ))}
    </div>
  );
}
