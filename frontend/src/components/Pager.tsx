import {
  Pagination,
  PaginationContent,
  PaginationEllipsis,
  PaginationItem,
  PaginationLink,
  PaginationNext,
  PaginationPrevious,
} from "@/components/ui/pagination";

function windowed(current: number, total: number): (number | "…")[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const pages: (number | "…")[] = [1];
  const start = Math.max(2, current - 1);
  const end = Math.min(total - 1, current + 1);
  if (start > 2) pages.push("…");
  for (let i = start; i <= end; i++) pages.push(i);
  if (end < total - 1) pages.push("…");
  pages.push(total);
  return pages;
}

interface PagerProps {
  page: number;
  totalPages: number;
  onPage: (page: number) => void;
}

export function Pager({ page, totalPages, onPage }: PagerProps) {
  if (totalPages <= 1) return null;
  const go = (p: number) => (e: React.MouseEvent) => {
    e.preventDefault();
    if (p >= 1 && p <= totalPages && p !== page) onPage(p);
  };

  return (
    <Pagination>
      <PaginationContent>
        <PaginationItem>
          <PaginationPrevious
            href="#"
            onClick={go(page - 1)}
            className={page === 1 ? "pointer-events-none opacity-40" : ""}
          />
        </PaginationItem>
        {windowed(page, totalPages).map((p, i) => (
          <PaginationItem key={`${p}-${i}`}>
            {p === "…" ? (
              <PaginationEllipsis />
            ) : (
              <PaginationLink href="#" isActive={p === page} onClick={go(p)}>
                {p}
              </PaginationLink>
            )}
          </PaginationItem>
        ))}
        <PaginationItem>
          <PaginationNext
            href="#"
            onClick={go(page + 1)}
            className={page === totalPages ? "pointer-events-none opacity-40" : ""}
          />
        </PaginationItem>
      </PaginationContent>
    </Pagination>
  );
}
