"use client";

import { SidebarNav } from "@/components/layout/sidebar-nav";
import { Header } from "@/components/layout/header";
import { PropertyProvider } from "@/components/providers/property-context";
import { isMockApiEnabled } from "@/lib/api";

export function AppShell({ children }: { children: React.ReactNode }) {
  const mock = isMockApiEnabled();

  return (
    <PropertyProvider>
      <div className="flex min-h-screen w-full">
        <SidebarNav />
        <div className="flex min-w-0 flex-1 flex-col">
          <Header />
          {mock ? (
            <div className="border-b border-amber-500/35 bg-amber-500/10 px-6 py-2 text-center text-xs text-amber-100/90">
              Demo mode: sample data only — no backend required. Set{" "}
              <code className="rounded bg-muted/50 px-1 py-0.5 font-mono text-[11px]">
                NEXT_PUBLIC_MOCK_API=1
              </code>{" "}
              on Vercel.
            </div>
          ) : null}
          <main className="flex-1 overflow-auto bg-background p-6">{children}</main>
        </div>
      </div>
    </PropertyProvider>
  );
}
