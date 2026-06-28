import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import {
  BarChart3,
  Building2,
  LayoutGrid,
  LogIn,
  LogOut,
  MapPin,
  Search,
  User,
} from "lucide-react";

import { logout } from "@/lib/auth-client";
import { useAuth } from "@/lib/useAuth";
import { useCity } from "@/lib/cityStore";
import { ClinicAvatar } from "@/components/ClinicAvatar";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupLabel,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";

interface NavItem {
  title: string;
  url: string;
  icon: typeof Search;
}
interface NavSection {
  label: string;
  items: NavItem[];
  adminOnly?: boolean;
}

const SECTIONS: NavSection[] = [
  {
    label: "Сервис",
    items: [
      { title: "Поиск", url: "/search", icon: Search },
      { title: "Клиники", url: "/clinics", icon: Building2 },
      { title: "Аналитика", url: "/analytics", icon: BarChart3 },
    ],
  },
  {
    label: "Аккаунт",
    items: [{ title: "Кабинет", url: "/cabinet", icon: User }],
  },
  {
    label: "Администрирование",
    adminOnly: true,
    items: [{ title: "Source Health", url: "/dashboard", icon: LayoutGrid }],
  },
];

function isActive(pathname: string, url: string): boolean {
  const route = url.split("#")[0] || "/";
  if (route === "/") return pathname === "/" || pathname.startsWith("/search");
  return pathname.startsWith(route);
}

export function AppSidebar() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { isAdmin, isAuthenticated, user } = useAuth();
  const { city } = useCity();

  const sections = SECTIONS.filter((s) => !s.adminOnly || isAdmin);

  const onLogout = () => {
    logout();
    navigate("/");
  };

  return (
    <Sidebar variant="inset" collapsible="offcanvas">
      <SidebarHeader>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton size="lg" asChild>
              <Link to="/">
                <img
                  src="/richard-without-background.png"
                  alt=""
                  className="size-8 shrink-0 object-contain"
                />
                <span className="text-[15px] font-semibold tracking-tight">
                  Richard Med
                </span>
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>

      <SidebarContent>
        {sections.map((section) => (
          <SidebarGroup key={section.label}>
            <SidebarGroupLabel>{section.label}</SidebarGroupLabel>
            <SidebarMenu>
              {section.items.map((item) => (
                <SidebarMenuItem key={item.url}>
                  <SidebarMenuButton
                    asChild
                    isActive={isActive(pathname, item.url)}
                    tooltip={item.title}
                  >
                    <NavLink to={item.url}>
                      <item.icon />
                      <span>{item.title}</span>
                    </NavLink>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroup>
        ))}
      </SidebarContent>

      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton className="pointer-events-none" tooltip={city}>
              <MapPin className="text-primary" />
              <span className="font-medium">{city}</span>
            </SidebarMenuButton>
          </SidebarMenuItem>
          {isAuthenticated ? (
            <SidebarMenuItem>
              <div className="mt-1 flex items-center gap-2 rounded-md border border-sidebar-border px-2 py-1.5">
                <ClinicAvatar name={user?.name || user?.email || "?"} size="sm" />
                <span className="min-w-0 flex-1 truncate text-sm text-foreground">
                  {user?.name || user?.email}
                </span>
                <button
                  type="button"
                  onClick={onLogout}
                  title="Выйти"
                  aria-label="Выйти"
                  className="shrink-0 rounded-md p-1 text-muted-foreground transition-colors hover:bg-secondary hover:text-foreground"
                >
                  <LogOut className="h-4 w-4" />
                </button>
              </div>
            </SidebarMenuItem>
          ) : (
            <SidebarMenuItem>
              <SidebarMenuButton asChild tooltip="Войти">
                <Link to="/login">
                  <LogIn />
                  <span>Войти</span>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          )}
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
