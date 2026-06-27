import { Link } from "react-router-dom";
import { Search } from "lucide-react";

import { Button } from "@/components/ui/button";
import { AppShell } from "@/components/AppShell";

export function NotFoundPage() {
  return (
    <AppShell breadcrumb={[{ label: "Страница не найдена" }]}>
      <div className="flex flex-1 flex-col items-center justify-center gap-4 px-6 py-24 text-center">
        <span className="flex h-14 w-14 items-center justify-center rounded-2xl bg-secondary">
          <Search className="h-6 w-6 text-faintest" />
        </span>
        <div>
          <h1 className="text-2xl font-semibold text-foreground">Страница не найдена</h1>
          <p className="mt-1 text-muted-foreground">
            Возможно, ссылка устарела или введена неверно.
          </p>
        </div>
        <Button asChild>
          <Link to="/">На главную</Link>
        </Button>
      </div>
    </AppShell>
  );
}
