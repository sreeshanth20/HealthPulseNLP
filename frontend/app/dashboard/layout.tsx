"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  Activity,
  ClipboardList,
  FlaskConical,
  HeartPulse,
  LogOut,
  Megaphone,
  Menu,
  ShieldCheck,
  Stethoscope,
  User,
  UserCog,
  X,
  ChevronRight,
} from "lucide-react";
import { Button } from "@/components/ui/core";
import { ThemeToggle } from "@/components/theme";
import { useAuth } from "@/lib/auth-context";
import { getToken, homeForRole } from "@/lib/api";
import { ROLE_LABELS, type Role } from "@/lib/types";
import { cn } from "@/lib/utils";

interface NavItem {
  href: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  roles: Role[];
  description: string;
}

const NAV: NavItem[] = [
  {
    href: "/dashboard/citizen",
    label: "Civic Complaints",
    icon: Megaphone,
    roles: ["CITIZEN", "SUPER_ADMIN"],
    description: "Submit & track civic reports",
  },
  {
    href: "/dashboard/patient",
    label: "My Health Reports",
    icon: HeartPulse,
    roles: ["PATIENT", "SUPER_ADMIN"],
    description: "Symptom logs & clinical docs",
  },
  {
    href: "/dashboard/clinician",
    label: "Clinical Triage",
    icon: Stethoscope,
    roles: ["CLINICIAN", "SUPER_ADMIN"],
    description: "Symptom review & entity triage",
  },
  {
    href: "/dashboard/municipal",
    label: "Complaint Operations",
    icon: ClipboardList,
    roles: ["MUNICIPAL_ADMIN", "SUPER_ADMIN"],
    description: "GIS map & resolution workflow",
  },
  {
    href: "/dashboard/health",
    label: "Health Intelligence",
    icon: FlaskConical,
    roles: ["HEALTH_ADMIN", "SUPER_ADMIN"],
    description: "Cross-domain scans & alerts",
  },
  {
    href: "/dashboard/superadmin",
    label: "System Administration",
    icon: UserCog,
    roles: ["SUPER_ADMIN"],
    description: "RBAC, telemetry & audit trail",
  },
];

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const { user, loading, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const [sidebarOpen, setSidebarOpen] = React.useState(false);

  // Authentication check
  React.useEffect(() => {
    if (!loading) {
      const token = getToken();
      if (!user || !token) {
        router.replace("/login");
      }
    }
  }, [loading, user, router]);

  // Role-based route enforcement
  React.useEffect(() => {
    if (user) {
      const currentNav = NAV.find((n) => pathname.startsWith(n.href));
      if (currentNav && !currentNav.roles.includes(user.role) && user.role !== "SUPER_ADMIN") {
        router.replace(homeForRole(user.role));
      }
    }
  }, [user, pathname, router]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#F7F8F6] dark:bg-[#102330]">
        <div className="text-center p-8 rounded-lg border border-[#E4EAE9] bg-white shadow-subtle dark:border-slate-800 dark:bg-[#142B3B]">
          <Activity className="mx-auto h-8 w-8 animate-pulse text-[#087F8C]" />
          <p className="mt-3 text-xs font-medium text-[#71818A] dark:text-slate-400">Verifying secure session…</p>
        </div>
      </div>
    );
  }

  const activeUser = user;
  if (!activeUser) return null;

  const visibleNav = NAV.filter((item) => item.roles.includes(activeUser.role));
  const roleLabel = ROLE_LABELS[activeUser.role] || activeUser.role;
  const currentNav = visibleNav.find((n) => pathname.startsWith(n.href));

  return (
    <div className="flex min-h-screen bg-[#F7F8F6] text-[#192D38] dark:bg-[#102330] dark:text-[#F7F8F6]">
      {/* Sidebar Desktop & Mobile Drawer */}
      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-40 w-64 border-r border-[#E4EAE9] bg-white transition-transform duration-200 ease-in-out md:static md:translate-x-0 dark:border-slate-800 dark:bg-[#142B3B] flex flex-col justify-between",
          sidebarOpen ? "translate-x-0" : "-translate-x-full"
        )}
      >
        <div>
          {/* Brand header */}
          <div className="flex h-16 items-center justify-between border-b border-[#E4EAE9] px-5 dark:border-slate-800">
            <Link href="/" className="flex items-center gap-2.5 font-bold tracking-tight text-[#142B3B] dark:text-white">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#087F8C] text-white shadow-sm">
                <Activity className="h-4.5 w-4.5" />
              </span>
              <div className="flex flex-col">
                <span className="text-sm font-extrabold leading-tight">
                  HealthPulse <span className="text-[#087F8C]">AI</span>
                </span>
                <span className="text-[10px] font-medium text-[#71818A] dark:text-slate-400 tracking-normal">
                  Enterprise Platform
                </span>
              </div>
            </Link>
            <button
              className="p-1 rounded-md text-[#71818A] hover:bg-[#F7F8F6] md:hidden dark:hover:bg-slate-800"
              onClick={() => setSidebarOpen(false)}
              aria-label="Close menu"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* User Profile Context */}
          <div className="border-b border-[#E4EAE9] px-5 py-3.5 bg-[#F7F8F6]/60 dark:border-slate-800 dark:bg-slate-900/40">
            <div className="flex items-center gap-3">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-[#DDF2F0] text-[#087F8C] font-semibold text-xs dark:bg-teal-950 dark:text-teal-300">
                {activeUser.full_name?.charAt(0) || "U"}
              </div>
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-bold text-[#192D38] dark:text-white">{activeUser.full_name}</p>
                <span className="inline-flex items-center rounded bg-[#DDF2F0] px-1.5 py-0.2 text-[10px] font-medium text-[#087F8C] dark:bg-teal-950 dark:text-teal-300">
                  {roleLabel}
                </span>
              </div>
            </div>
          </div>

          {/* Role Navigation */}
          <div className="px-3 py-3">
            <p className="px-3 pb-2 text-[10px] font-bold uppercase tracking-wider text-[#71818A] dark:text-slate-400">
              Workspaces & Modules
            </p>
            <nav className="space-y-1">
              {visibleNav.map((item) => {
                const active = pathname.startsWith(item.href);
                const Icon = item.icon;
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    onClick={() => setSidebarOpen(false)}
                    className={cn(
                      "group flex items-center gap-3 rounded-md px-3 py-2 text-xs font-medium transition-all relative",
                      active
                        ? "bg-[#DDF2F0] text-[#087F8C] font-semibold dark:bg-teal-950/60 dark:text-teal-300"
                        : "text-[#71818A] hover:bg-[#F7F8F6] hover:text-[#192D38] dark:text-slate-400 dark:hover:bg-slate-800 dark:hover:text-white"
                    )}
                  >
                    {active && (
                      <span className="absolute left-0 top-1.5 bottom-1.5 w-1 rounded-r bg-[#087F8C]" />
                    )}
                    <Icon className={cn("h-4 w-4 shrink-0", active ? "text-[#087F8C] dark:text-teal-300" : "text-[#71818A] group-hover:text-[#192D38] dark:text-slate-400 dark:group-hover:text-white")} />
                    <div className="min-w-0 flex-1">
                      <p className="truncate leading-tight">{item.label}</p>
                    </div>
                  </Link>
                );
              })}
            </nav>
          </div>
        </div>

        {/* Responsible AI Disclaimer badge */}
        <div className="p-4 border-t border-[#E4EAE9] dark:border-slate-800">
          <div className="rounded-lg border border-[#E4EAE9] bg-[#F7F8F6] p-3 text-[11px] leading-relaxed text-[#71818A] dark:border-slate-800 dark:bg-slate-900/60 dark:text-slate-400">
            <div className="flex items-center gap-1.5 font-semibold text-[#142B3B] dark:text-teal-300 mb-1">
              <ShieldCheck className="h-3.5 w-3.5 text-[#087F8C]" />
              <span>Surveillance Notice</span>
            </div>
            Signals indicate statistical co-occurrence. All alerts require ground verification.
          </div>
        </div>
      </aside>

      {/* Backdrop for mobile */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-[#142B3B]/60 backdrop-blur-xs md:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Main Content Area */}
      <div className="flex min-w-0 flex-1 flex-col">
        {/* Sticky Header */}
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-[#E4EAE9] bg-white/95 px-5 backdrop-blur dark:border-slate-800 dark:bg-[#142B3B]/95">
          <div className="flex items-center gap-3">
            <button
              className="p-1.5 rounded-md text-[#71818A] hover:bg-[#F7F8F6] md:hidden dark:hover:bg-slate-800"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open menu"
            >
              <Menu className="h-5 w-5" />
            </button>
            <div className="hidden sm:flex items-center gap-2 text-xs text-[#71818A] dark:text-slate-400">
              <span className="font-medium text-[#192D38] dark:text-white">HealthPulse AI</span>
              <ChevronRight className="h-3.5 w-3.5 text-[#71818A]" />
              <span className="font-semibold text-[#087F8C] dark:text-teal-300">
                {currentNav?.label ?? "Dashboard"}
              </span>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <span className="hidden lg:inline-flex items-center gap-1.5 rounded-full border border-emerald-200 bg-emerald-50 px-2.5 py-0.5 text-[11px] font-medium text-emerald-800 dark:border-emerald-800 dark:bg-emerald-950/40 dark:text-emerald-300">
              <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
              Intelligence Engine Active
            </span>
            <ThemeToggle />
            <Button
              variant="outline"
              size="sm"
              onClick={logout}
              className="h-8 gap-1.5 border-[#E4EAE9] text-xs font-medium text-[#192D38] hover:bg-[#F7F8F6] dark:border-slate-800 dark:text-slate-300 dark:hover:bg-slate-800"
            >
              <LogOut className="h-3.5 w-3.5" /> Sign out
            </Button>
          </div>
        </header>

        {/* Page Body */}
        <main className="flex-1 p-5 md:p-8 max-w-7xl w-full mx-auto">{children}</main>
      </div>
    </div>
  );
}
