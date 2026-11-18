"use client";

import * as React from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  Activity,
  ArrowLeft,
  CheckCircle2,
  HeartPulse,
  Lock,
  Mail,
  Megaphone,
  Phone,
  ShieldCheck,
  User,
} from "lucide-react";
import { Alert, Button, Input, Label, Select } from "@/components/ui/core";
import { api, homeForRole, storeSession } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";
import type { User as UserType } from "@/lib/types";

export default function RegisterPage() {
  const router = useRouter();
  const { setUser } = useAuth();

  const [fullName, setFullName] = React.useState("");
  const [email, setEmail] = React.useState("");
  const [phone, setPhone] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [confirm, setConfirm] = React.useState("");
  const [role, setRole] = React.useState<"CITIZEN" | "PATIENT">("CITIZEN");
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (password !== confirm) {
      setError("Passwords do not match.");
      return;
    }
    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    setLoading(true);
    try {
      const payload: Record<string, string> = {
        email: email.trim().toLowerCase(),
        password,
        full_name: fullName.trim(),
        role,
      };
      if (phone.trim()) payload.phone = phone.trim();

      const response = await api.post<{ access_token: string; user: UserType }>("/auth/register", payload);
      storeSession(response.access_token, response.user);
      setUser(response.user);
      router.push(homeForRole(response.user.role));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex min-h-screen bg-[#F7F8F6] text-[#192D38] dark:bg-[#102330] dark:text-[#F7F8F6]">
      {/* Left Column: Brand & Security Overview */}
      <div className="hidden lg:flex lg:w-1/2 flex-col justify-between bg-[#142B3B] p-12 text-white relative overflow-hidden">
        <div className="absolute inset-0 opacity-10 bg-[radial-gradient(#087F8C_1px,transparent_1px)] [background-size:20px_20px] pointer-events-none" />

        <div className="relative z-10">
          <Link href="/" className="inline-flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-[#087F8C] text-white shadow-sm">
              <Activity className="h-6 w-6" />
            </span>
            <div>
              <span className="text-xl font-bold tracking-tight">HealthPulse <span className="text-[#087F8C]">AI</span></span>
              <p className="text-xs text-[#9BB0BC]">Citizen & Patient Portal Enrollment</p>
            </div>
          </Link>

          <div className="mt-16 max-w-lg">
            <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl leading-tight">
              Join the community health intelligence network.
            </h1>
            <p className="mt-4 text-sm leading-relaxed text-[#9BB0BC]">
              Create an account to report localized environmental complaints or submit voluntary symptom histories to safeguard community health.
            </p>
          </div>

          <div className="mt-10 space-y-4 max-w-md">
            <div className="flex items-start gap-3 rounded-lg border border-[#203A4A] bg-[#1a3344]/50 p-3.5">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-[#087F8C]/20 text-[#DDF2F0]">
                <Megaphone className="h-4 w-4" />
              </div>
              <div className="text-xs">
                <p className="font-semibold text-white">As a Citizen</p>
                <p className="mt-0.5 text-[#9BB0BC]">Submit water, sewage, garbage, air pollution, and pest complaints with intelligent auto-categorization and duplicate alerts.</p>
              </div>
            </div>

            <div className="flex items-start gap-3 rounded-lg border border-[#203A4A] bg-[#1a3344]/50 p-3.5">
              <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded bg-[#087F8C]/20 text-[#DDF2F0]">
                <HeartPulse className="h-4 w-4" />
              </div>
              <div className="text-xs">
                <p className="font-semibold text-white">As a Patient</p>
                <p className="mt-0.5 text-[#9BB0BC]">Securely log symptoms, upload medical prescriptions or lab summaries, and help detect early public health concerns.</p>
              </div>
            </div>
          </div>
        </div>

        <div className="relative z-10 border-t border-[#203A4A] pt-4 text-xs text-[#71818A]">
          <p className="flex items-center gap-1.5 font-medium text-[#9BB0BC]">
            <ShieldCheck className="h-4 w-4 text-[#087F8C]" />
            Privacy-Preserving Healthcare Architecture
          </p>
          <p className="mt-1 text-[11px] leading-relaxed">
            Staff roles (clinician, municipal officer, health administrator) are provisioned through administrative governance.
          </p>
        </div>
      </div>

      {/* Right Column: Registration Form */}
      <div className="flex flex-1 flex-col justify-center px-6 py-12 lg:px-16 xl:px-24">
        <div className="mx-auto w-full max-w-md">
          <Link href="/login" className="mb-6 inline-flex items-center gap-2 text-xs text-[#71818A] hover:text-[#192D38] dark:hover:text-white transition-colors">
            <ArrowLeft className="h-3.5 w-3.5" /> Back to sign in
          </Link>

          <div className="mb-6">
            <h2 className="text-2xl font-bold tracking-tight text-[#192D38] dark:text-white">Create an Account</h2>
            <p className="mt-1 text-xs text-[#71818A] dark:text-slate-400">
              Select your role to start using HealthPulse AI.
            </p>
          </div>

          {error && <Alert variant="destructive" className="mb-4 text-xs">{error}</Alert>}

          <form onSubmit={onSubmit} className="space-y-3.5">
            <div className="space-y-1">
              <Label htmlFor="name" className="text-xs font-semibold text-[#192D38] dark:text-slate-300">
                Full Name
              </Label>
              <div className="relative">
                <Input
                  id="name"
                  required
                  minLength={2}
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="e.g. Jane Doe"
                  className="pl-9 h-9 border-[#E4EAE9] bg-white text-xs dark:border-slate-700 dark:bg-slate-900 focus-visible:ring-[#087F8C]"
                />
                <User className="absolute left-3 top-2.5 h-4 w-4 text-[#71818A]" />
              </div>
            </div>

            <div className="space-y-1">
              <Label htmlFor="email" className="text-xs font-semibold text-[#192D38] dark:text-slate-300">
                Email Address
              </Label>
              <div className="relative">
                <Input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  className="pl-9 h-9 border-[#E4EAE9] bg-white text-xs dark:border-slate-700 dark:bg-slate-900 focus-visible:ring-[#087F8C]"
                />
                <Mail className="absolute left-3 top-2.5 h-4 w-4 text-[#71818A]" />
              </div>
            </div>

            <div className="space-y-1">
              <Label htmlFor="phone" className="text-xs font-semibold text-[#192D38] dark:text-slate-300">
                Phone Number (optional)
              </Label>
              <div className="relative">
                <Input
                  id="phone"
                  value={phone}
                  onChange={(e) => setPhone(e.target.value)}
                  placeholder="+1 (555) 000-0000"
                  className="pl-9 h-9 border-[#E4EAE9] bg-white text-xs dark:border-slate-700 dark:bg-slate-900 focus-visible:ring-[#087F8C]"
                />
                <Phone className="absolute left-3 top-2.5 h-4 w-4 text-[#71818A]" />
              </div>
            </div>

            <div className="space-y-1">
              <Label htmlFor="role" className="text-xs font-semibold text-[#192D38] dark:text-slate-300">
                Primary Account Purpose
              </Label>
              <Select
                id="role"
                value={role}
                onChange={(e) => setRole(e.target.value as "CITIZEN" | "PATIENT")}
                className="h-9 border-[#E4EAE9] bg-white text-xs dark:border-slate-700 dark:bg-slate-900 focus-visible:ring-[#087F8C]"
              >
                <option value="CITIZEN">Citizen — Report civic and environmental issues</option>
                <option value="PATIENT">Patient — Submit voluntary symptom reports & clinical documents</option>
              </Select>
            </div>

            <div className="grid gap-3 sm:grid-cols-2">
              <div className="space-y-1">
                <Label htmlFor="password" className="text-xs font-semibold text-[#192D38] dark:text-slate-300">
                  Password
                </Label>
                <div className="relative">
                  <Input
                    id="password"
                    type="password"
                    required
                    minLength={8}
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Min 8 characters"
                    className="pl-9 h-9 border-[#E4EAE9] bg-white text-xs dark:border-slate-700 dark:bg-slate-900 focus-visible:ring-[#087F8C]"
                  />
                  <Lock className="absolute left-3 top-2.5 h-4 w-4 text-[#71818A]" />
                </div>
              </div>
              <div className="space-y-1">
                <Label htmlFor="confirm" className="text-xs font-semibold text-[#192D38] dark:text-slate-300">
                  Confirm Password
                </Label>
                <div className="relative">
                  <Input
                    id="confirm"
                    type="password"
                    required
                    minLength={8}
                    value={confirm}
                    onChange={(e) => setConfirm(e.target.value)}
                    placeholder="Confirm password"
                    className="pl-9 h-9 border-[#E4EAE9] bg-white text-xs dark:border-slate-700 dark:bg-slate-900 focus-visible:ring-[#087F8C]"
                  />
                  <Lock className="absolute left-3 top-2.5 h-4 w-4 text-[#71818A]" />
                </div>
              </div>
            </div>

            <Button
              type="submit"
              className="w-full h-10 mt-2 bg-[#087F8C] hover:bg-[#066873] text-white font-medium text-xs shadow-sm transition-colors"
              loading={loading}
            >
              Complete Registration
            </Button>
          </form>

          <p className="mt-4 text-center text-xs text-[#71818A]">
            Already have an account?{" "}
            <Link href="/login" className="font-semibold text-[#087F8C] hover:underline">
              Sign in
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
