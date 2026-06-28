import { useNavigate } from "react-router-dom";
import { LogOut, Mail, Shield, User } from "lucide-react";

import { logout } from "@/lib/auth-client";
import { useAuth } from "@/lib/useAuth";
import { AppShell } from "@/components/AppShell";

export function CabinetPage() {
  const navigate = useNavigate();
  const { user, isAdmin } = useAuth();

  const onLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <AppShell breadcrumb={[{ label: "Кабинет" }]}>
      <div className="mx-auto max-w-2xl px-4 py-8">
        <div className="rounded-2xl border border-border bg-white p-6 shadow-sm">
          <div className="flex items-center gap-4">
            <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-accent text-primary">
              <User className="h-7 w-7" />
            </div>
            <div className="min-w-0">
              <div className="truncate text-lg font-semibold text-foreground">
                {user?.name || "Пользователь"}
              </div>
              <div className="truncate text-sm text-muted-foreground">{user?.email}</div>
            </div>
            {isAdmin && (
              <span className="ml-auto shrink-0 rounded-full bg-accent px-3 py-1 text-xs font-medium text-primary">
                Админ
              </span>
            )}
          </div>

          <div className="mt-6 space-y-2 border-t border-secondary pt-5 text-sm text-muted-foreground">
            <div className="flex items-center gap-2">
              <Mail className="h-4 w-4 shrink-0" /> {user?.email}
            </div>
            <div className="flex items-center gap-2">
              <Shield className="h-4 w-4 shrink-0" /> Роль:{" "}
              {isAdmin ? "администратор" : "пользователь"}
            </div>
          </div>

          <button
            onClick={onLogout}
            className="mt-6 flex items-center gap-2 rounded-lg border border-border px-4 py-2 text-sm text-muted-foreground transition-colors hover:bg-secondary"
          >
            <LogOut className="h-4 w-4" /> Выйти
          </button>
        </div>
        <p className="mt-4 text-xs text-muted-foreground">
          Сохранённые услуги, история поиска и уведомления о ценах — скоро.
        </p>
      </div>
    </AppShell>
  );
}
