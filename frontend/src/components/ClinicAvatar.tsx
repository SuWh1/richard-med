const SIZES = {
  sm: "w-7 h-7 text-[11px]",
  md: "w-9 h-9 text-sm",
  lg: "w-12 h-12 text-base",
} as const;

const PALETTE = ["#0E9F8E", "#6366F1", "#F59E0B", "#EC4899", "#8B5CF6", "#0EA5E9"];

function initialsOf(name: string): string {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((w) => w[0]?.toUpperCase() ?? "")
    .join("");
}

function colorOf(name: string): string {
  let hash = 0;
  for (const ch of name) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0;
  return PALETTE[hash % PALETTE.length];
}

interface ClinicAvatarProps {
  name: string;
  size?: keyof typeof SIZES;
}

export function ClinicAvatar({ name, size = "md" }: ClinicAvatarProps) {
  return (
    <div
      className={`${SIZES[size]} flex shrink-0 items-center justify-center rounded-full font-semibold text-white`}
      style={{ background: colorOf(name) }}
      aria-hidden
    >
      {initialsOf(name)}
    </div>
  );
}
