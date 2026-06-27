import type { ReactNode } from "react";

export type StatusVariant = "success" | "warning" | "error" | "neutral";

const VARIANTS: Record<StatusVariant, string> = {
  success: "bg-[#DCFCE7] text-[#16A34A]",
  warning: "bg-[#FEF3C7] text-[#D97706]",
  error: "bg-[#FEE2E2] text-[#DC2626]",
  neutral: "bg-[#F1F5F9] text-[#475569]",
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
