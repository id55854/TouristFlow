"use client";

import { SidebarNav } from "@/components/layout/sidebar-nav";
import { Header } from "@/components/layout/header";
import { PropertyProvider } from "@/components/providers/property-context";

export function AppShell({ children }: { children: React.ReactNode }) {
  return (
    <PropertyProvider>
      <div className="flex min-h-screen w-full">
        <SidebarNav />
        <div className="flex min-w-0 flex-1 flex-col">
          <Header />
          <main className="flex-1 overflow-auto bg-background p-6">{children}</main>
        </div>
      </div>
    </PropertyProvider>
  );
}
