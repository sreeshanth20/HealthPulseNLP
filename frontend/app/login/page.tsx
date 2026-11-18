"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  Activity,
  ArrowRight,
  CheckCircle2,
  Eye,
  EyeOff,
  FileText,
  FlaskConical,
  HeartPulse,
  Lock,
  Mail,
  Megaphone,
  ShieldCheck,
  Stethoscope,
  UserCheck,
  Users,
} from "lucide-react";
import { Alert, Button, Input, Label } from "@/components/ui/core";
import { useAuth } from "@/lib/auth-context";
import { homeForRole } from "@/lib/api";
import { ROLE_LABELS, type Role } from "@/lib/types";

interface DemoAccount {
  role: Role;
  label: string;
  email: string;
  subtitle: string;
  icon: React.ComponentType<{ className?: string }>;
}

const DEMO_ACCOUNTS: DemoAccount[] = [
  {
    role: "CITIZEN",
    label: "Citizen",
    email: "citizen@healthpulse.demo",
    subtitle: "Civic complaints & duplicates",
    icon: Megaphone,
  },
  {
    role: "PATIENT",
    label: "Patient",
    email: "patient@healthpulse.demo",
    subtitle: "Symptom logs & medical vault",
    icon: HeartPulse,
  },
  {
    role: "CLINICIAN",
    label: "Healthcare Professional",
    email: "clinician@healthpulse.demo",
    subtitle: "Clinical NER & triage review",
    icon: Stethoscope,
  },
  {
    role: "MUNICIPAL_ADMIN",
    label: "Municipal Administrator",
    email: "municipal@healthpulse.demo",
    subtitle: "Operations & GIS heatmap",
    icon: Users,
  },
  {
    role: "HEALTH_ADMIN",
    label: "Public Health Administrator",
    email: "health@healthpulse.demo",
    subtitle: "Cross-domain scans & alerts",
    icon: FlaskConical,
  },
  {
    role: "SUPER_ADMIN",
    label: "Super Administrator",
    email: "super@healthpulse.demo",
    subtitle: "Full RBAC, telemetry & audit",
    icon: ShieldCheck,
  },
];

function LoginForm() {
  const router = useRouter();
  const params = useSearchParams();
  const { login } = useAuth();

  const [email, setEmail] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [showPassword, setShowPassword] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);
  const [selectedRole, setSelectedRole] = React.useState<string | null>(null);

  const expired = params.get("expired") === "1";

  async function handleAuthenticate(targetEmail?: string, targetPassword?: string) {
    const e = (targetEmail || email).trim();
    const p = targetPassword || password;
    if (!e || !p) {
      setError("Please provide both email and password.");
      return;
    }
    setError(null);
    setLoading(true);
    try {
      const user = await login(e, p);
      router.push(homeForRole(user.role));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Authentication failed. Please verify credentials.");
    } finally {
      setLoading(false);
    }
  }

  function handleFormSubmit(e: React.FormEvent) {
    e.preventDefault();
    handleAuthenticate();
  }

  function selectDemoAccount(acc: DemoAccount) {
    setEmail(acc.email);
    setPassword("HealthPulse!2026");
    setSelectedRole(acc.role);
    setError(null);
  }

  return (
    <div className="flex min-h-screen bg-[#F7F8F6] text-[#192D38] dark:bg-[#102330] dark:text-[#F7F8F6]">
      {/* Left Column: Brand & Enterprise Value Proposition */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-between bg-[#142B3B] p-12 text-white relative overflow-hidden">
        {/* Subtle patterned overlay */}
        <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#087F8C_1px,transparent_1px)] [background-size:20px_20px] pointer-events-none" />

        {/* Brand identity */}
        <div className="relative z-10">
          <Link href="/" className="inline-flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#087F8C] text-white shadow-sm">
              <Activity className="h-6 w-6" />
            </span>
            <div>
              <span className="text-xl font-bold tracking-tight">HealthPulse <span className="text-[#087F8C]">AI</span></span>
              <p className="text-xs text-[#9BB0BC]">Enterprise Healthcare & Civic Intelligence</p>
            </div>
          </Link>

          <div className="mt-16 max-w-lg">
            <span className="inline-flex items-center gap-2 rounded-full border border-[#203A4A] bg-[#203A4A]/60 px-3 py-1 text-xs font-medium text-[#DDF2F0]">
              <CheckCircle2 className="h-3.5 w-3.5 text-[#087F8C]" />
              Dual-Domain Early Warning Platform
            </span>
            <h1 className="mt-4 text-3xl font-extrabold tracking-tight sm:text-4xl leading-tight">
              Evidence-backed community health & environmental surveillance.
            </h1>
            <p className="mt-4 text-sm leading-relaxed text-[#9BB0BC]">
              Bridging municipal civic grievances with voluntary clinical symptoms to detect correlated public health risks before they become outbreaks.
            </p>
          </div>

          {/* Value pillars */}
          <div className="mt-10 space-y-4 max-w-md">
            <div className="flex items-start gap-3 rounded-lg border border-[#203A4A] bg-[#1a3344]/50 p-3.5">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-[#087F8C]/20 text-[#DDF2F0]">
                <Megaphone className="h-4 w-4" />
              </div>
              <div className="text-xs">
                <p className="font-semibold text-white">Civic & Environmental NLP</p>
                <p className="mt-0.5 text-[#9BB0BC]">On-device zero-leakage classification across 10 environmental categories with automated duplicate mitigation.</p>
              </div>
            </div>

            <div className="flex items-start gap-3 rounded-lg border border-[#203A4A] bg-[#1a3344]/50 p-3.5">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-[#087F8C]/20 text-[#DDF2F0]">
                <Stethoscope className="h-4 w-4" />
              </div>
              <div className="text-xs">
                <p className="font-semibold text-white">Clinical Entity Recognition</p>
                <p className="mt-0.5 text-[#9BB0BC]">De-identified symptom extraction from text and PDF clinical documentation with explainable triage scoring.</p>
              </div>
            </div>

            <div className="flex items-start gap-3 rounded-lg border border-[#203A4A] bg-[#1a3344]/50 p-3.5">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-[#087F8C]/20 text-[#DDF2F0]">
                <FlaskConical className="h-4 w-4" />
              </div>
              <div className="text-xs">
                <p className="font-semibold text-white">Cross-Domain Intelligence</p>
                <p className="mt-0.5 text-[#9BB0BC]">Spatio-temporal co-occurrence matrix flagging joint civic and health anomalies for official investigation.</p>
              </div>
            </div>
          </div>
        </div>

        {/* Responsible AI compliance footer */}
        <div className="relative z-10 border-t border-[#203A4A] pt-4 text-xs text-[#71818A]">
          <p className="flex items-center gap-1.5 font-medium text-[#9BB0BC]">
            <ShieldCheck className="h-4 w-4 text-[#087F8C]" />
            Strict Enterprise Compliance & Responsible AI
          </p>
          <p className="mt-1 text-[11px] leading-relaxed">
            All correlation signals represent statistical co-occurrence indicators for official investigation. Non-diagnostic and non-causal.
          </p>
        </div>
      </div>

      {/* Right Column: Authentication Card & Demo Role Selector */}
      <div className="flex flex-1 flex-col justify-center px-6 py-12 lg:px-16 xl:px-24">
        <div className="mx-auto w-full max-w-md">
          {/* Mobile brand header */}
          <div className="mb-8 flex items-center justify-between lg:hidden">
            <Link href="/" className="flex items-center gap-2 font-bold text-[#142B3B] dark:text-white">
              <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[#087F8C] text-white">
                <Activity className="h-4.5 w-4.5" />
              </span>
              <span>HealthPulse <span className="text-[#087F8C]">AI</span></span>
            </Link>
            <Link href="/" className="text-xs text-[#71818A] hover:text-[#192D38]">Back to home</Link>
          </div>

          <div className="mb-6">
            <h2 className="text-2xl font-bold tracking-tight text-[#192D38] dark:text-white">Sign in to your account</h2>
            <p className="mt-1.5 text-xs text-[#71818A] dark:text-slate-400">
              Access your role-specific dashboard using organizational credentials.
            </p>
          </div>

          {expired && (
            <Alert variant="warning" className="mb-4 text-xs">
              Your previous session expired. Please sign in again.
            </Alert>
          )}

          {error && (
            <Alert variant="destructive" className="mb-4 text-xs">
              {error}
            </Alert>
          )}

          <form onSubmit={handleFormSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="email" className="text-xs font-semibold text-[#192D38] dark:text-slate-300">
                Email Address
              </Label>
              <div className="relative">
                <Input
                  id="email"
                  type="email"
                  required
                  placeholder="name@healthpulse.demo"
                  value={email}
                  onChange={(e) => {
                    setEmail(e.target.value);
                    setSelectedRole(null);
                  }}
                  className="pl-9 h-10 border-[#E4EAE9] bg-white text-xs dark:border-slate-700 dark:bg-slate-900 focus-visible:ring-[#087F8C]"
                />
                <Mail className="absolute left-3 top-3 h-4 w-4 text-[#71818A]" />
              </div>
            </div>

            <div className="space-y-1.5">
              <div className="flex items-center justify-between">
                <Label htmlFor="password" className="text-xs font-semibold text-[#192D38] dark:text-slate-300">
                  Password
                </Label>
                <span className="text-[11px] text-[#71818A]">Demo: HealthPulse!2026</span>
              </div>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  required
                  placeholder="••••••••••••"
                  value={password}
                  onChange={(e) => {
                    setPassword(e.target.value);
                    setSelectedRole(null);
                  }}
                  className="pl-9 pr-10 h-10 border-[#E4EAE9] bg-white text-xs dark:border-slate-700 dark:bg-slate-900 focus-visible:ring-[#087F8C]"
                />
                <Lock className="absolute left-3 top-3 h-4 w-4 text-[#71818A]" />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-3 text-[#71818A] hover:text-[#192D38] dark:hover:text-white"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              className="w-full h-10 bg-[#087F8C] hover:bg-[#066873] text-white font-medium text-xs shadow-sm transition-colors"
              loading={loading}
            >
              Sign In
            </Button>
          </form>

          <p className="mt-4 text-center text-xs text-[#71818A]">
            Don&apos;t have an account?{" "}
            <Link href="/register" className="font-semibold text-[#087F8C] hover:underline">
              Create citizen / patient account
            </Link>
          </p>

          {/* Demo Role Selector */}
          <div className="mt-8 rounded-lg border border-[#E4EAE9] bg-white p-4 shadow-subtle dark:border-slate-800 dark:bg-[#142B3B]">
            <div className="mb-3 flex items-center justify-between">
              <span className="text-xs font-bold uppercase tracking-wider text-[#142B3B] dark:text-teal-300">
                Quick Demo Authentication
              </span>
              <span className="rounded bg-[#DDF2F0] px-2 py-0.5 text-[10px] font-semibold text-[#087F8C] dark:bg-teal-950 dark:text-teal-300">
                6 Verified Roles
              </span>
            </div>
            <p className="text-[11px] text-[#71818A] dark:text-slate-400 mb-3 leading-relaxed">
              Click any role to autofill verified demo credentials and authenticate through the live backend API.
            </p>

            <div className="grid grid-cols-2 gap-2 text-xs">
              {DEMO_ACCOUNTS.map((acc) => {
                const Icon = acc.icon;
                const active = selectedRole === acc.role;
                return (
                  <button
                    key={acc.email}
                    type="button"
                    onClick={() => selectDemoAccount(acc)}
                    className={`flex items-start gap-2.5 rounded-md border p-2.5 text-left transition-all ${
                      active
                        ? "border-[#087F8C] bg-[#DDF2F0]/40 text-[#142B3B] dark:bg-teal-950/50 dark:text-teal-200 dark:border-teal-500 ring-1 ring-[#087F8C]"
                        : "border-[#E4EAE9] bg-[#F7F8F6] text-[#192D38] hover:border-[#087F8C]/60 hover:bg-white dark:border-slate-800 dark:bg-slate-900/60 dark:text-slate-300"
                    }`}
                  >
                    <div className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded ${
                      active ? "bg-[#087F8C] text-white" : "bg-white text-[#087F8C] border border-[#E4EAE9] dark:bg-slate-800 dark:border-slate-700"
                    }`}>
                      <Icon className="h-3.5 w-3.5" />
                    </div>
                    <div className="min-w-0">
                      <p className="truncate font-semibold text-[11px] leading-tight">{acc.label}</p>
                      <p className="truncate text-[10px] text-[#71818A] dark:text-slate-400 mt-0.5">{acc.subtitle}</p>
                    </div>
                  </button>
                );
              })}
            </div>

            {selectedRole && (
              <div className="mt-3 pt-3 border-t border-[#E4EAE9] dark:border-slate-800 flex items-center justify-between">
                <span className="text-[11px] text-[#71818A] dark:text-slate-400">
                  Ready to authenticate as <strong className="text-[#192D38] dark:text-white">{selectedRole}</strong>
                </span>
                <Button
                  size="sm"
                  onClick={() => handleAuthenticate()}
                  loading={loading}
                  className="h-7 text-xs bg-[#087F8C] hover:bg-[#066873] text-white px-3"
                >
                  Sign In <ArrowRight className="h-3 w-3 ml-1" />
                </Button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <React.Suspense>
      <LoginForm />
    </React.Suspense>
  );
}
