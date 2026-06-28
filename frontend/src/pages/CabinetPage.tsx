import { type ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { Bell, Bookmark, Clock, LogOut, Mail, Shield, User } from "lucide-react";

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
    <AppShell breadcrumb={[{ label: "Поиск", href: "/" }, { label: "Кабинет" }]}>
      <div className="mx-auto w-full max-w-[1400px] px-4 py-8 lg:px-6">
        <header className="mb-6">
          <h1 className="text-xl font-semibold text-foreground">Личный кабинет</h1>
          <p className="text-sm text-muted-foreground">
            Профиль, сохранённые услуги и уведомления о ценах
          </p>
        </header>

        <div className="grid gap-4 lg:grid-cols-3">
          <ProfileCard
            name={user?.name || "Пользователь"}
            email={user?.email}
            isAdmin={isAdmin}
            onLogout={onLogout}
          />

          <div className="grid gap-4 sm:grid-cols-2 lg:col-span-2">
            <CabinetSection
              icon={<Bookmark className="h-4 w-4" />}
              title="Сохранённые услуги"
              hint="Сохраняйте услуги, чтобы быстро сравнивать цены позже."
            />
            <CabinetSection
              icon={<Clock className="h-4 w-4" />}
              title="История поиска"
              hint="Здесь появятся ваши недавние запросы."
            />
            <CabinetSection
              icon={<Bell className="h-4 w-4" />}
              title="Уведомления о ценах"
              hint="Сообщим, когда цена на услугу изменится."
              className="sm:col-span-2"
            />
          </div>
        </div>
      </div>
    </AppShell>
  );
}

function ProfileCard({
  name,
  email,
  isAdmin,
  onLogout,
}: {
  name: string;
  email: string | undefined;
  isAdmin: boolean;
  onLogout: () => void;
}) {
  return (
    <div className="rounded-2xl border border-border bg-white p-6 shadow-sm lg:col-span-1">
      <div className="flex items-center gap-4">
        <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-full bg-accent text-primary">
          <User className="h-7 w-7" />
        </div>
        <div className="min-w-0">
          <div className="truncate text-lg font-semibold text-foreground">{name}</div>
          <div className="truncate text-sm text-muted-foreground">{email}</div>
        </div>
        {isAdmin && (
          <span className="ml-auto shrink-0 rounded-full bg-accent px-3 py-1 text-xs font-medium text-primary">
            Админ
          </span>
        )}
      </div>

      <div className="mt-6 space-y-2 border-t border-secondary pt-5 text-sm text-muted-foreground">
        <div className="flex items-center gap-2">
          <Mail className="h-4 w-4 shrink-0" /> {email}
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
  );
}

interface CabinetSectionProps {
  icon: ReactNode;
  title: string;
  hint: string;
  className?: string;
  children?: ReactNode;
}

function CabinetSection({ icon, title, hint, className, children }: CabinetSectionProps) {
  return (
    <section
      className={`flex flex-col rounded-2xl border border-border bg-white p-5 shadow-sm ${className ?? ""}`}
    >
      <div className="mb-4 flex items-center gap-2">
        <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-accent text-primary">
          {icon}
        </span>
        <h2 className="font-semibold text-foreground">{title}</h2>
        <span className="ml-auto rounded-full bg-secondary px-2 py-0.5 text-[11px] font-medium text-muted-foreground">
          Скоро
        </span>
      </div>
      {children ?? (
        <div className="flex flex-1 items-center justify-center rounded-xl border border-dashed border-border bg-secondary/40 px-4 py-8 text-center text-sm text-muted-foreground">
          {hint}
        </div>
      )}
    </section>
  );
}
