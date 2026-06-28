import { Link, NavLink, useLocation, useNavigate } from "react-router-dom";
import {
  BarChart3,
  LayoutGrid,
  LogIn,
  LogOut,
  MapPin,
  Search,
  User,
} from "lucide-react";

import { logout } from "@/lib/auth-client";
import { useAuth } from "@/lib/useAuth";
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

const NAV = [
  { title: "Поиск", url: "/", icon: Search },
  { title: "Аналитика", url: "/analytics", icon: BarChart3 },
  { title: "Кабинет", url: "/cabinet", icon: User },
];
const ADMIN_NAV = [{ title: "Source Health", url: "/dashboard", icon: LayoutGrid }];

function isActive(pathname: string, url: string): boolean {
  if (url === "/") return pathname === "/" || pathname.startsWith("/search");
  return pathname.startsWith(url);
}

export function AppSidebar({ city = "Астана" }: { city?: string }) {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { isAdmin, isAuthenticated, user } = useAuth();

  // Source Health is admin-only — non-admins never even see the link.
  const items = isAdmin ? [...NAV, ...ADMIN_NAV] : NAV;

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
        <SidebarGroup>
          <SidebarGroupLabel>Навигация</SidebarGroupLabel>
          <SidebarMenu>
            {items.map((item) => (
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
                <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-accent text-xs font-semibold uppercase text-primary">
                  {(user?.name || user?.email || "?").charAt(0)}
                </span>
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
