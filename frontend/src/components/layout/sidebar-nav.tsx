"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  CalendarDays,
  Coins,
  LayoutDashboard,
  LineChart,
  Sparkles,
  Building2,
  Wand2,
  Layers,
} from "lucide-react";
import { cn } from "@/lib/utils";

const items = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/portfolio", label: "Portfolio fusion", icon: Layers },
  { href: "/forecast", label: "Forecast", icon: LineChart },
  { href: "/pricing", label: "Pricing", icon: Coins },
  { href: "/competitors", label: "Competitors", icon: Building2 },
  { href: "/simulator", label: "Simulator", icon: Wand2 },
  { href: "/calendar", label: "Calendar", icon: CalendarDays },
  { href: "/insights", label: "AI Insights", icon: Sparkles },
];

export function SidebarNav() {
  const pathname = usePathname();

  return (
    <aside className="flex w-56 shrink-0 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground">
      <div className="flex h-14 items-center border-b border-sidebar-border px-4">
        <Link href="/" className="flex items-center gap-2 font-semibold tracking-tight">
          <BarChart3 className="h-6 w-6 text-sidebar-primary" />
          <span>TouristFlow</span>
        </Link>
      </div>
      <nav className="flex flex-1 flex-col gap-0.5 p-2">
        {items.map(({ href, label, icon: Icon }) => {
          const active = pathname === href || (href !== "/" && pathname.startsWith(href));
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-sidebar-foreground/80 hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground"
              )}
            >
              <Icon className="h-4 w-4 shrink-0" />
              {label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
