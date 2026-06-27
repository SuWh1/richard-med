import { Link, NavLink, useLocation } from "react-router-dom";
import { BarChart3, LayoutGrid, MapPin, Search } from "lucide-react";

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
  { title: "Кабинет", url: "/dashboard", icon: LayoutGrid },
];

function isActive(pathname: string, url: string): boolean {
  if (url === "/") return pathname === "/" || pathname.startsWith("/search");
  return pathname.startsWith(url);
}

export function AppSidebar({ city = "Астана" }: { city?: string }) {
  const { pathname } = useLocation();

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
            {NAV.map((item) => (
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
            <SidebarMenuButton
              className="pointer-events-none"
              tooltip={`Казахстан · ${city}`}
            >
              <MapPin className="text-primary" />
              <span className="flex flex-col leading-tight">
                <span className="text-[11px] text-muted-foreground">Казахстан</span>
                <span className="font-medium">{city}</span>
              </span>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
    </Sidebar>
  );
}
