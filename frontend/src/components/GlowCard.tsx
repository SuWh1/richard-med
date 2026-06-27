import type { ReactNode } from "react";

import { cn } from "@/components/ui/utils";

interface GlowCardProps {
  children: ReactNode;
  className?: string;
}

/** Card shell with an always-on rotating black glow border. */
export function GlowCard({ children, className }: GlowCardProps) {
  return (
    <div
      className={cn(
        "relative rounded-xl border border-border bg-card shadow-sm",
        className,
      )}
    >
      <span aria-hidden className="glow-ring" />
      <div className="relative z-10 h-full rounded-[inherit]">{children}</div>
    </div>
  );
}
