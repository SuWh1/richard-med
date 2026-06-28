import { Fragment, type ReactNode } from "react";
import { Link } from "react-router-dom";
import { ChevronLeft } from "lucide-react";

import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from "@/components/ui/breadcrumb";
import { Separator } from "@/components/ui/separator";
import {
  SidebarInset,
  SidebarProvider,
  SidebarTrigger,
} from "@/components/ui/sidebar";
import { AppSidebar } from "./AppSidebar";

export interface Crumb {
  label: string;
  href?: string;
}

interface AppShellProps {
  breadcrumb: Crumb[];
  city?: string;
  headerRight?: ReactNode;
  children: ReactNode;
}

function readSidebarOpen(): boolean {
  if (typeof document === "undefined") return true;
  const match = document.cookie.match(/(?:^|;\s*)sidebar_state=([^;]+)/);
  return match ? match[1] === "true" : true;
}

export function AppShell({ breadcrumb, city, headerRight, children }: AppShellProps) {
  const parent = [...breadcrumb].reverse().find((c) => c.href);
  const current = breadcrumb[breadcrumb.length - 1];

  return (
    <SidebarProvider defaultOpen={readSidebarOpen()} className="h-svh overflow-hidden">
      <AppSidebar city={city} />
      <SidebarInset className="overflow-hidden bg-inset">
        <header className="z-30 flex h-14 shrink-0 items-center gap-2 px-4">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mr-1 data-[orientation=vertical]:h-4" />

          {/* Mobile: one-tap back to the nearest clickable step */}
          {parent ? (
            <Link
              to={parent.href!}
              className="flex min-w-0 items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground md:hidden"
            >
              <ChevronLeft className="h-4 w-4 shrink-0" />
              <span className="truncate">{parent.label}</span>
            </Link>
          ) : (
            <span className="truncate text-sm font-medium text-foreground md:hidden">
              {current?.label}
            </span>
          )}

          {/* Desktop: full clickable trail */}
          <Breadcrumb className="hidden md:block">
            <BreadcrumbList>
              {breadcrumb.map((crumb, i) => {
                const last = i === breadcrumb.length - 1;
                return (
                  <Fragment key={`${crumb.label}-${i}`}>
                    <BreadcrumbItem>
                      {last || !crumb.href ? (
                        <BreadcrumbPage>{crumb.label}</BreadcrumbPage>
                      ) : (
                        <BreadcrumbLink asChild>
                          <Link to={crumb.href}>{crumb.label}</Link>
                        </BreadcrumbLink>
                      )}
                    </BreadcrumbItem>
                    {!last && <BreadcrumbSeparator />}
                  </Fragment>
                );
              })}
            </BreadcrumbList>
          </Breadcrumb>
          {headerRight && <div className="ml-auto flex items-center gap-2">{headerRight}</div>}
        </header>
        <div className="flex flex-1 flex-col overflow-y-auto">{children}</div>
      </SidebarInset>
    </SidebarProvider>
  );
}
