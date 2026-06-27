import { AlertTriangle, X } from "lucide-react";

interface StaleBannerProps {
  onDismiss: () => void;
}

export function StaleBanner({ onDismiss }: StaleBannerProps) {
  return (
    <div className="border-b border-warning/30 bg-warning-soft">
      <div className="mx-auto flex w-full max-w-[1440px] items-center gap-2 px-5 py-2.5">
        <AlertTriangle className="h-4 w-4 shrink-0 text-warning" />
        <span className="text-sm text-warning-strong">
          Некоторые цены могут быть устаревшими. Проверяйте источник перед записью.
        </span>
        <button
          type="button"
          onClick={onDismiss}
          aria-label="Закрыть"
          className="ml-auto text-warning transition-colors hover:text-warning-strong"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
