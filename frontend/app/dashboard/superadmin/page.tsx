"use client";

import * as React from "react";
import {
  Activity,
  AlertTriangle,
  BrainCircuit,
  CheckCircle2,
  Database,
  Download,
  FileText,
  Filter,
  HardDrive,
  Layers,
  Lock,
  RefreshCw,
  ScrollText,
  Search,
  ServerCog,
  ShieldAlert,
  ShieldCheck,
  UserCheck,
  UserCog,
  Users,
  XCircle,
} from "lucide-react";
import {
  Alert,
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
  Label,
  Select,
  Separator,
} from "@/components/ui/core";
import {
  EmptyState,
  ErrorState,
  LoadingState,
  PaginationBar,
  StatCard,
} from "@/components/dashboard-widgets";
import { CategoryPie, SimpleBarChart } from "@/components/charts";
import { useToast } from "@/components/ui/toast";
import { api, API_URL, getToken } from "@/lib/api";
import type { AuditEntry, DashboardStats, Page, User } from "@/lib/types";
import { formatDateTime, titleCase } from "@/lib/utils";

const ROLES = ["CITIZEN", "PATIENT", "CLINICIAN", "MUNICIPAL_ADMIN", "HEALTH_ADMIN", "SUPER_ADMIN"];

interface SystemHealth {
  database: { ok: boolean; counts: Record<string, number> };
  cache: string;
  nlp_pipeline: { embedder: string; classifier: string; ner: string; transformers_available: boolean };
  document_storage: { root: string; used_mb: number };
  environment: string;
}

export default function SuperAdminDashboard() {
  const [tab, setTab] = React.useState<"users" | "audit" | "system">("users");

  return (
    <div className="space-y-6">
      {/* Header section */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-[#E4EAE9] pb-5 dark:border-slate-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#192D38] dark:text-white">
            System Administration & Audit Headquarters
          </h1>
          <p className="mt-1 text-xs text-[#71818A] dark:text-slate-400">
            Enterprise RBAC governance, immutable security audit trail, and ML inference pipeline telemetry.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-1.5 rounded-lg border border-[#E4EAE9] bg-white p-1 shadow-subtle dark:border-slate-800 dark:bg-slate-900">
          {([
            ["users", "User Management & RBAC", <UserCog key="i" className="h-3.5 w-3.5 mr-1" />],
            ["audit", "Security Audit Trail", <ScrollText key="i" className="h-3.5 w-3.5 mr-1" />],
            ["system", "System Diagnostics", <ServerCog key="i" className="h-3.5 w-3.5 mr-1" />],
          ] as const).map(([key, label, icon]) => (
            <button
              key={key}
              onClick={() => setTab(key as "users" | "audit" | "system")}
              className={`flex items-center rounded-md px-3 py-1.5 text-xs font-semibold transition-colors ${
                tab === key
                  ? "bg-[#087F8C] text-white shadow-xs"
                  : "text-[#71818A] hover:text-[#192D38] dark:hover:text-white"
              }`}
            >
              {icon} {label}
            </button>
          ))}
        </div>
      </div>

      {tab === "users" && <UsersView />}
      {tab === "audit" && <AuditView />}
      {tab === "system" && <SystemView />}
    </div>
  );
}

/* ---------------------------------- Users ----------------------------------- */
function UsersView() {
  const { toast } = useToast();
  const [users, setUsers] = React.useState<Page<User> | null>(null);
  const [stats, setStats] = React.useState<DashboardStats | null>(null);
  const [page, setPage] = React.useState(1);
  const [q, setQ] = React.useState("");
  const [role, setRole] = React.useState("");
  const [busyId, setBusyId] = React.useState<number | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const load = React.useCallback(async () => {
    setLoading(true);
    try {
      const query = new URLSearchParams({ page: String(page), page_size: "12" });
      if (q) query.set("q", q);
      if (role) query.set("role", role);
      const [list, overview] = await Promise.all([
        api.get<Page<User>>(`/users?${query.toString()}`),
        api.get<DashboardStats>("/analytics/overview"),
      ]);
      setUsers(list);
      setStats(overview);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load user list");
    } finally {
      setLoading(false);
    }
  }, [page, q, role]);

  React.useEffect(() => {
    load();
  }, [load]);

  async function updateUser(u: User, patch: { role?: string; is_active?: boolean }) {
    setBusyId(u.id);
    try {
      await api.patch(`/users/${u.id}`, patch);
      toast(`User #${u.id} updated successfully`, { variant: "success" });
      load();
    } catch (err) {
      toast("Update failed", {
        variant: "error",
        description: err instanceof Error ? err.message : undefined,
      });
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="space-y-6">
      {/* Metric Cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard
          label="Registered Users"
          value={stats?.total_users ?? "—"}
          hint="Enrolled platform identities"
          icon={<Users className="h-5 w-5" />}
        />
        <StatCard
          label="Active Authorized Accounts"
          value={stats?.active_users ?? "—"}
          hint="Permitted authentication state"
          icon={<UserCheck className="h-5 w-5 text-emerald-600" />}
        />
        <StatCard
          label="Role Groups Represented"
          value={Object.keys(stats?.users_by_role ?? {}).length}
          hint="Across all 6 stakeholder roles"
          icon={<ShieldCheck className="h-5 w-5 text-[#087F8C]" />}
        />
      </div>

      {Object.keys(stats?.users_by_role ?? {}).length > 0 && (
        <Card className="border-[#E4EAE9] bg-white shadow-subtle dark:border-slate-800 dark:bg-[#142B3B]">
          <CardHeader className="border-b border-[#E4EAE9] pb-3 dark:border-slate-800">
            <CardTitle className="text-sm font-bold text-[#192D38] dark:text-white">
              Role Distribution Matrix
            </CardTitle>
            <CardDescription className="text-xs text-[#71818A] dark:text-slate-400">
              Breakdown of registered accounts by organizational function.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 pt-5">
            <CategoryPie data={stats?.users_by_role ?? {}} />
          </CardContent>
        </Card>
      )}

      {/* User Management Table */}
      <Card className="border-[#E4EAE9] bg-white shadow-subtle dark:border-slate-800 dark:bg-[#142B3B]">
        <CardHeader className="border-b border-[#E4EAE9] pb-4 dark:border-slate-800">
          <div className="grid gap-3 sm:grid-cols-12 items-end">
            <div className="sm:col-span-6 space-y-1">
              <Label htmlFor="uq" className="text-xs font-semibold text-[#192D38] dark:text-slate-300">
                Search Name or Email
              </Label>
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-[#71818A]" />
                <Input
                  id="uq"
                  placeholder="Filter users..."
                  value={q}
                  onChange={(e) => {
                    setQ(e.target.value);
                    setPage(1);
                  }}
                  className="pl-8 h-8 text-xs border-[#E4EAE9] dark:border-slate-700 dark:bg-slate-900"
                />
              </div>
            </div>

            <div className="sm:col-span-4 space-y-1">
              <Label htmlFor="urole" className="text-xs font-semibold text-[#192D38] dark:text-slate-300">
                Filter by Role
              </Label>
              <Select
                id="urole"
                value={role}
                onChange={(e) => {
                  setRole(e.target.value);
                  setPage(1);
                }}
                className="h-8 text-xs border-[#E4EAE9] dark:border-slate-700 dark:bg-slate-900"
              >
                <option value="">All Roles</option>
                {ROLES.map((r) => (
                  <option key={r} value={r}>
                    {titleCase(r.toLowerCase())}
                  </option>
                ))}
              </Select>
            </div>

            <div className="sm:col-span-2">
              <Button
                variant="outline"
                size="sm"
                onClick={load}
                className="h-8 w-full border-[#E4EAE9] text-xs hover:bg-[#F7F8F6] dark:border-slate-700"
              >
                <RefreshCw className="h-3.5 w-3.5 mr-1 text-[#087F8C]" /> Refresh
              </Button>
            </div>
          </div>
        </CardHeader>

        <CardContent className="p-0">
          {error ? (
            <div className="p-6">
              <ErrorState message={error} retry={load} />
            </div>
          ) : loading ? (
            <LoadingState label="Loading registered platform users…" />
          ) : !users || users.items.length === 0 ? (
            <div className="p-6">
              <EmptyState title="No users found" description="No accounts match current search criteria." />
            </div>
          ) : (
            <div className="divide-y divide-[#E4EAE9] dark:divide-slate-800">
              {users.items.map((u) => (
                <div
                  key={u.id}
                  className="p-4 sm:p-5 flex flex-col md:flex-row md:items-center justify-between gap-3 hover:bg-[#F7F8F6]/60 transition-colors dark:hover:bg-slate-900/30"
                >
                  <div className="min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <div className="flex h-7 w-7 items-center justify-center rounded-full bg-[#DDF2F0] text-[#087F8C] font-semibold text-xs dark:bg-teal-950 dark:text-teal-300">
                        {u.full_name?.charAt(0) || "U"}
                      </div>
                      <span className="font-bold text-xs text-[#192D38] dark:text-white">{u.full_name}</span>
                      <span
                        className={`rounded px-1.5 py-0.2 text-[10px] font-semibold border ${
                          u.is_active
                            ? "bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950 dark:text-emerald-300 dark:border-emerald-800"
                            : "bg-rose-50 text-rose-800 border-rose-200 dark:bg-rose-950 dark:text-rose-300"
                        }`}
                      >
                        {u.is_active ? "Active" : "Disabled"}
                      </span>
                    </div>

                    <p className="text-xs text-[#71818A] dark:text-slate-400">
                      {u.email} · Enrolled {formatDateTime(u.created_at)} · Last Login:{" "}
                      {u.last_login_at ? formatDateTime(u.last_login_at) : "Never"}
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    <select
                      className="h-8 rounded-md border border-[#E4EAE9] bg-white px-2.5 text-xs text-[#192D38] dark:border-slate-700 dark:bg-slate-900 dark:text-white"
                      value={u.role}
                      disabled={busyId === u.id}
                      onChange={(e) => updateUser(u, { role: e.target.value })}
                    >
                      {ROLES.map((r) => (
                        <option key={r} value={r}>
                          {titleCase(r.toLowerCase())}
                        </option>
                      ))}
                    </select>

                    <Button
                      size="sm"
                      variant={u.is_active ? "destructive" : "default"}
                      loading={busyId === u.id}
                      onClick={() => updateUser(u, { is_active: !u.is_active })}
                      className="h-8 text-xs px-3"
                    >
                      {u.is_active ? "Disable" : "Enable"}
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="p-4 border-t border-[#E4EAE9] dark:border-slate-800">
            {users && <PaginationBar page={users.page} pages={users.pages} onPage={setPage} />}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

/* --------------------------------- Audit log -------------------------------- */
function AuditView() {
  const [logs, setLogs] = React.useState<Page<AuditEntry> | null>(null);
  const [page, setPage] = React.useState(1);
  const [action, setAction] = React.useState("");
  const [q, setQ] = React.useState("");
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const load = React.useCallback(async () => {
    setLoading(true);
    try {
      const query = new URLSearchParams({ page: String(page), page_size: "25" });
      if (action) query.set("action", action);
      if (q) query.set("q", q);
      setLogs(await api.get<Page<AuditEntry>>(`/audit-logs?${query.toString()}`));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load audit trail");
    } finally {
      setLoading(false);
    }
  }, [page, action, q]);

  React.useEffect(() => {
    load();
  }, [load]);

  const knownActions = [
    "auth.login",
    "auth.register",
    "complaint.create",
    "complaint.status",
    "complaint.mark_duplicate",
    "report.create",
    "report.summarize",
    "document.upload",
    "document.delete",
    "alert.status",
    "investigation.create",
    "investigation.update",
    "intelligence.scan",
    "user.role_change",
    "user.activation",
    "analytics.export",
  ];

  return (
    <Card className="border-[#E4EAE9] bg-white shadow-subtle dark:border-slate-800 dark:bg-[#142B3B]">
      <CardHeader className="border-b border-[#E4EAE9] pb-4 dark:border-slate-800">
        <div className="grid gap-3 sm:grid-cols-12 items-end">
          <div className="sm:col-span-4 space-y-1">
            <Label htmlFor="aact" className="text-xs font-semibold text-[#192D38] dark:text-slate-300">
              Filter by Action Type
            </Label>
            <Select
              id="aact"
              value={action}
              onChange={(e) => {
                setAction(e.target.value);
                setPage(1);
              }}
              className="h-8 text-xs border-[#E4EAE9] dark:border-slate-700 dark:bg-slate-900"
            >
              <option value="">All Action Events</option>
              {knownActions.map((a) => (
                <option key={a} value={a}>
                  {a}
                </option>
              ))}
            </Select>
          </div>

          <div className="sm:col-span-6 space-y-1">
            <Label htmlFor="aq" className="text-xs font-semibold text-[#192D38] dark:text-slate-300">
              Search Event Detail / Payload
            </Label>
            <div className="relative">
              <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-[#71818A]" />
              <Input
                id="aq"
                value={q}
                onChange={(e) => {
                  setQ(e.target.value);
                  setPage(1);
                }}
                placeholder="e.g. Millbrook, role, IP..."
                className="pl-8 h-8 text-xs border-[#E4EAE9] dark:border-slate-700 dark:bg-slate-900"
              />
            </div>
          </div>

          <div className="sm:col-span-2">
            <Button
              variant="outline"
              size="sm"
              onClick={load}
              className="h-8 w-full border-[#E4EAE9] text-xs hover:bg-[#F7F8F6] dark:border-slate-700"
            >
              <RefreshCw className="h-3.5 w-3.5 mr-1 text-[#087F8C]" /> Refresh
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-0">
        {error ? (
          <div className="p-6">
            <ErrorState message={error} retry={load} />
          </div>
        ) : loading ? (
          <LoadingState label="Inspecting cryptographically sequenced audit logs…" />
        ) : !logs || logs.items.length === 0 ? (
          <div className="p-6">
            <EmptyState title="No matching audit entries" description="Clear filter parameters to inspect the trail." />
          </div>
        ) : (
          <div className="overflow-x-auto scroll-thin">
            <table className="w-full text-left text-xs">
              <thead>
                <tr className="border-b border-[#E4EAE9] bg-[#F7F8F6] text-[11px] font-bold uppercase tracking-wider text-[#71818A] dark:border-slate-800 dark:bg-slate-900/60 dark:text-slate-400">
                  <th className="px-4 py-3">Timestamp</th>
                  <th className="px-4 py-3">Actor & Role</th>
                  <th className="px-4 py-3">Action Event</th>
                  <th className="px-4 py-3">Target Entity</th>
                  <th className="px-4 py-3">Origin IP</th>
                  <th className="px-4 py-3">Audit Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-[#E4EAE9] dark:divide-slate-800">
                {logs.items.map((log) => (
                  <tr key={log.id} className="hover:bg-[#F7F8F6]/50 dark:hover:bg-slate-900/40 transition-colors">
                    <td className="whitespace-nowrap px-4 py-2.5 font-mono text-[11px] text-[#71818A] dark:text-slate-400">
                      {formatDateTime(log.created_at)}
                    </td>
                    <td className="px-4 py-2.5 font-medium text-[#192D38] dark:text-white">
                      {log.actor_role ?? "SYSTEM"} #{log.actor_id ?? "0"}
                    </td>
                    <td className="px-4 py-2.5">
                      <span className="font-mono text-[11px] font-semibold text-[#087F8C] bg-[#DDF2F0] px-2 py-0.5 rounded border border-[#B2E4E0] dark:bg-teal-950 dark:text-teal-300 dark:border-teal-800">
                        {log.action}
                      </span>
                    </td>
                    <td className="px-4 py-2.5 text-[11px] text-[#71818A] dark:text-slate-300">
                      {log.entity_type} {log.entity_id ? `(#${log.entity_id})` : ""}
                    </td>
                    <td className="px-4 py-2.5 font-mono text-[11px] text-[#71818A]">
                      {log.ip || "127.0.0.1"}
                    </td>
                    <td className="max-w-[280px] truncate px-4 py-2.5 font-mono text-[11px] text-[#71818A] dark:text-slate-400">
                      {log.detail ?? "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div className="p-4 border-t border-[#E4EAE9] dark:border-slate-800">
          {logs && <PaginationBar page={logs.page} pages={logs.pages} onPage={setPage} />}
        </div>
      </CardContent>
    </Card>
  );
}

/* ------------------------------- System health ------------------------------ */
function SystemView() {
  const [health, setHealth] = React.useState<SystemHealth | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const load = React.useCallback(async () => {
    setLoading(true);
    try {
      setHealth(await api.get<SystemHealth>("/system/health"));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load system health diagnostics");
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    load();
  }, [load]);

  if (loading) return <LoadingState label="Checking system health telemetry…" />;
  if (error || !health) return <ErrorState message={error ?? "Unknown diagnostic error"} retry={load} />;

  return (
    <div className="space-y-6">
      {/* Telemetry Cards */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Database Cluster"
          value={health.database.ok ? "Healthy" : "Degraded"}
          hint={`${health.database.counts.users ?? 0} users · ${health.database.counts.complaints ?? 0} complaints`}
          icon={<Database className="h-5 w-5 text-emerald-600" />}
        />
        <StatCard
          label="In-Memory Cache"
          value={titleCase(health.cache)}
          hint="Fast local memory fallback"
          icon={<Activity className="h-5 w-5 text-[#087F8C]" />}
        />
        <StatCard
          label="Embedder Engine"
          value={health.nlp_pipeline.embedder.split(":")[0]}
          hint={health.nlp_pipeline.embedder}
          icon={<BrainCircuit className="h-5 w-5 text-indigo-600" />}
        />
        <StatCard
          label="Classification Model"
          value={health.nlp_pipeline.classifier}
          hint="TF-IDF Logistic Classifier"
          icon={<ServerCog className="h-5 w-5 text-purple-600" />}
        />
      </div>

      {/* Diagnostics Card */}
      <Card className="border-[#E4EAE9] bg-white shadow-subtle dark:border-slate-800 dark:bg-[#142B3B]">
        <CardHeader className="border-b border-[#E4EAE9] pb-3 dark:border-slate-800">
          <CardTitle className="text-sm font-bold text-[#192D38] dark:text-white flex items-center gap-2">
            <ShieldCheck className="h-4 w-4 text-emerald-600" /> ML Inference Pipeline Telemetry
          </CardTitle>
          <CardDescription className="text-xs text-[#71818A] dark:text-slate-400">
            Runtime ML components and storage subsystems.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-5 space-y-3 text-xs">
          <div className="grid gap-3 sm:grid-cols-2">
            <div className="rounded-md border border-[#E4EAE9] p-3 dark:border-slate-800">
              <span className="font-bold text-[#192D38] dark:text-white">Active Embedder:</span>
              <p className="font-mono mt-1 text-[#087F8C]">{health.nlp_pipeline.embedder}</p>
            </div>
            <div className="rounded-md border border-[#E4EAE9] p-3 dark:border-slate-800">
              <span className="font-bold text-[#192D38] dark:text-white">Medical NER Backend:</span>
              <p className="font-mono mt-1 text-[#087F8C]">{health.nlp_pipeline.ner}</p>
            </div>
            <div className="rounded-md border border-[#E4EAE9] p-3 dark:border-slate-800">
              <span className="font-bold text-[#192D38] dark:text-white">Document Vault Storage:</span>
              <p className="font-mono mt-1 text-[#192D38] dark:text-white">{health.document_storage.used_mb} MB Allocated</p>
            </div>
            <div className="rounded-md border border-[#E4EAE9] p-3 dark:border-slate-800">
              <span className="font-bold text-[#192D38] dark:text-white">Environment Mode:</span>
              <p className="font-mono mt-1 text-[#192D38] dark:text-white">{health.environment.toUpperCase()}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Database Entity Distribution */}
      <Card className="border-[#E4EAE9] bg-white shadow-subtle dark:border-slate-800 dark:bg-[#142B3B]">
        <CardHeader className="border-b border-[#E4EAE9] pb-3 dark:border-slate-800">
          <CardTitle className="text-sm font-bold text-[#192D38] dark:text-white">
            Database Record Volumes by Entity Model
          </CardTitle>
          <CardDescription className="text-xs text-[#71818A] dark:text-slate-400">
            Current live record counts stored in persistence layer.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-4 pt-5">
          <SimpleBarChart
            horizontal
            data={Object.entries(health.database.counts).map(([name, value]) => ({
              name: titleCase(name),
              value,
            }))}
          />
        </CardContent>
      </Card>
    </div>
  );
}
