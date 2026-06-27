import { Fragment, type ReactNode } from "react";
import { Link } from "react-router-dom";

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
  return (
    <SidebarProvider defaultOpen={readSidebarOpen()} className="h-svh overflow-hidden">
      <AppSidebar city={city} />
      <SidebarInset className="overflow-hidden bg-inset">
        <header className="z-30 flex h-14 shrink-0 items-center gap-2 px-4">
          <SidebarTrigger className="-ml-1" />
          <Separator orientation="vertical" className="mr-1 data-[orientation=vertical]:h-4" />
          <Breadcrumb>
            <BreadcrumbList>
              {breadcrumb.map((crumb, i) => {
                const last = i === breadcrumb.length - 1;
                return (
                  <Fragment key={`${crumb.label}-${i}`}>
                    <BreadcrumbItem className={last ? "" : "hidden md:block"}>
                      {last || !crumb.href ? (
                        <BreadcrumbPage>{crumb.label}</BreadcrumbPage>
                      ) : (
                        <BreadcrumbLink asChild>
                          <Link to={crumb.href}>{crumb.label}</Link>
                        </BreadcrumbLink>
                      )}
                    </BreadcrumbItem>
                    {!last && <BreadcrumbSeparator className="hidden md:block" />}
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
