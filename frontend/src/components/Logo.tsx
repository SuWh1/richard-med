import { Link } from "react-router-dom";

import { cn } from "@/components/ui/utils";

interface LogoProps {
  className?: string;
}

export function Logo({ className }: LogoProps) {
  return (
    <Link to="/" className={cn("flex shrink-0 items-center gap-2.5", className)}>
      <img
        src="/richard-without-background.png"
        alt="Richard Med"
        className="h-11 w-auto shrink-0 object-contain"
      />
      <span className="hidden text-[15px] font-semibold tracking-tight text-foreground sm:inline">
        Richard Med
      </span>
    </Link>
  );
}
