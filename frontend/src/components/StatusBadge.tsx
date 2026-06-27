import type { ReactNode } from "react";

export type StatusVariant = "success" | "warning" | "error" | "neutral";

const VARIANTS: Record<StatusVariant, string> = {
  success: "bg-success-soft text-success",
  warning: "bg-warning-soft text-warning",
  error: "bg-danger-soft text-danger",
  neutral: "bg-secondary text-secondary-foreground",
};

interface StatusBadgeProps {
  variant: StatusVariant;
  children: ReactNode;
}

export function StatusBadge({ variant, children }: StatusBadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-[11px] font-medium ${VARIANTS[variant]}`}
    >
      {children}
    </span>
  );
}
