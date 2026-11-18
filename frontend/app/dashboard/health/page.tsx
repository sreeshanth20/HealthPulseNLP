"use client";

import * as React from "react";
import {
  Activity,
  AlertTriangle,
  BrainCircuit,
  CheckCircle2,
  ChevronRight,
  Download,
  FileText,
  Filter,
  FlaskConical,
  Layers,
  Loader2,
  MapPin,
  RefreshCw,
  ScanSearch,
  Search,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Syringe,
  X,
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
  Textarea,
} from "@/components/ui/core";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  DisclaimerNote,
  EmptyState,
  ErrorState,
  EvidencePanel,
  LoadingState,
  PaginationBar,
  StatCard,
  StatusBadge,
  UrgencyBadge,
} from "@/components/dashboard-widgets";
import { HeatMap, type MapPoint } from "@/components/map/heatmap";
import { CategoryPie, SimpleBarChart, TrendChart } from "@/components/charts";
import { useToast } from "@/components/ui/toast";
import { api, API_URL, getToken } from "@/lib/api";
import type { Alert as AlertType, AlertEvidence, DashboardStats, Investigation, Page } from "@/lib/types";
import { formatDateTime, titleCase } from "@/lib/utils";

export default function HealthAdminDashboard() {
  const [stats, setStats] = React.useState<DashboardStats | null>(null);
  const [alerts, setAlerts] = React.useState<Page<AlertType>>({ items: [], total: 0, page: 1, page_size: 10, pages: 1 });
  const [investigations, setInvestigations] = React.useState<Page<Investigation>>({ items: [], total: 0, page: 1, page_size: 10, pages: 1 });
  const [points, setPoints] = React.useState<MapPoint[]>([]);
  const [scanning, setScanning] = React.useState(false);
  const [alertStatus, setAlertStatus] = React.useState("");
  const [selected, setSelected] = React.useState<AlertType | null>(null);
  const [alertPage, setAlertPage] = React.useState(1);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [tab, setTab] = React.useState<"overview" | "alerts" | "investigations">("overview");
  const { toast } = useToast();

  const load = React.useCallback(async () => {
    setLoading(true);
    try {
      const q = new URLSearchParams({ page: String(alertPage), page_size: "10" });
      if (alertStatus) q.set("status", alertStatus);
      const [overview, alertPageData, invPage, geo] = await Promise.all([
        api.get<DashboardStats>("/analytics/overview"),
        api.get<Page<AlertType>>(`/alerts?${q.toString()}`),
        api.get<Page<Investigation>>("/investigations?page_size=10"),
        api.get<{ points: MapPoint[] }>("/analytics/heatmap?days=90"),
      ]);
      setStats(overview);
      setAlerts(alertPageData);
      setInvestigations(invPage);
      setPoints(geo.points);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load public health intelligence");
    } finally {
      setLoading(false);
    }
  }, [alertPage, alertStatus]);

  React.useEffect(() => {
    load();
  }, [load]);

  async function runScan() {
    setScanning(true);
    try {
      const result = await api.post<{ alerts_created: number; scan: { candidate_pairs: number } }>(
        "/intelligence/scan",
        { days: 30 }
      );
      toast(`Cross-domain intelligence scan complete`, {
        variant: "success",
        description: `${result.alerts_created} alert(s) generated from ${result.scan.candidate_pairs} candidate pairs.`,
      });
      load();
    } catch (err) {
      toast("Scan execution failed", {
        variant: "error",
        description: err instanceof Error ? err.message : undefined,
      });
    } finally {
      setScanning(false);
    }
  }

  async function exportCsv(dataset: "complaints" | "reports" | "alerts") {
    try {
      const res = await fetch(`${API_URL}/analytics/export?dataset=${dataset}`, {
        headers: { Authorization: `Bearer ${getToken()}` },
      });
      if (!res.ok) throw new Error(`Export failed (${res.status})`);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `healthpulse_${dataset}.csv`;
      a.click();
      URL.revokeObjectURL(url);
      toast(`Exported ${dataset} CSV`, { variant: "success" });
    } catch (err) {
      toast("Export failed", {
        variant: "error",
        description: err instanceof Error ? err.message : undefined,
      });
    }
  }

  return (
    <div className="space-y-6">
      {/* Header section */}
      <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between border-b border-[#E4EAE9] pb-5 dark:border-slate-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#192D38] dark:text-white">
            Public Health Intelligence & Outbreak Surveillance
          </h1>
          <p className="mt-1 text-xs text-[#71818A] dark:text-slate-400">
            Spatio-temporal intelligence linking civic environmental grievances with voluntary clinical symptoms for epidemic early warning.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          <Button
            onClick={runScan}
            loading={scanning}
            className="h-8.5 bg-[#087F8C] hover:bg-[#066873] text-white text-xs font-semibold shadow-sm px-3.5"
          >
            <ScanSearch className="h-3.5 w-3.5 mr-1.5" /> Run Correlation Scan
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => exportCsv("reports")}
            className="h-8.5 border-[#E4EAE9] text-xs hover:bg-[#F7F8F6] dark:border-slate-800"
          >
            <Download className="h-3.5 w-3.5 mr-1" /> Export Reports CSV
          </Button>
        </div>
      </div>

      <DisclaimerNote />

      {/* Tab bar */}
      <div className="flex items-center gap-1.5 rounded-lg border border-[#E4EAE9] bg-white p-1 shadow-subtle dark:border-slate-800 dark:bg-slate-900 w-fit">
        {([
          ["overview", "Overview & Analytics", <Activity key="i" className="h-3.5 w-3.5 mr-1" />],
          ["alerts", "Correlation Alerts", <BrainCircuit key="i" className="h-3.5 w-3.5 mr-1" />],
          ["investigations", "Field Investigations", <Layers key="i" className="h-3.5 w-3.5 mr-1" />],
        ] as const).map(([key, label, icon]) => (
          <button
            key={key}
            onClick={() => setTab(key as "overview" | "alerts" | "investigations")}
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

      {error && tab !== "overview" ? (
        <ErrorState message={error} retry={load} />
      ) : loading ? (
        <LoadingState label="Synthesizing public health epidemiological data…" />
      ) : tab === "overview" ? (
        error ? <ErrorState message={error} retry={load} /> : <Overview stats={stats} points={points} />
      ) : tab === "alerts" ? (
        <AlertsView
          alerts={alerts}
          statusFilter={alertStatus}
          setStatusFilter={(v) => {
            setAlertStatus(v);
            setAlertPage(1);
          }}
          onPage={setAlertPage}
          onSelect={setSelected}
          onChanged={load}
        />
      ) : (
        <InvestigationsView investigations={investigations} onChanged={load} />
      )}

      {selected && (
        <AlertDetail alert={selected} onClose={() => setSelected(null)} onChanged={load} />
      )}
    </div>
  );
}

/* --------------------------------- Overview --------------------------------- */
function Overview({ stats, points }: { stats: DashboardStats | null; points: MapPoint[] }) {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          label="Voluntary Health Reports"
          value={stats?.total_reports ?? "—"}
          hint={`${stats?.reports_last_14d ?? 0} logged past 14 days`}
          icon={<FlaskConical className="h-5 w-5" />}
        />
        <StatCard
          label="Active Correlation Alerts"
          value={stats?.open_alerts ?? "—"}
          hint="Under review & confirmed"
          icon={<BrainCircuit className="h-5 w-5 text-amber-600" />}
        />
        <StatCard
          label="Field Investigations"
          value={stats?.open_investigations ?? "—"}
          hint="Active sampling & site visits"
          icon={<Layers className="h-5 w-5 text-[#087F8C]" />}
        />
        <StatCard
          label="Civic Environmental Reports"
          value={stats?.complaints_last_14d ?? "—"}
          hint="Correlated civic inputs"
          icon={<Activity className="h-5 w-5" />}
        />
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="border-[#E4EAE9] bg-white shadow-subtle dark:border-slate-800 dark:bg-[#142B3B]">
          <CardHeader className="border-b border-[#E4EAE9] pb-3 dark:border-slate-800">
            <CardTitle className="text-sm font-bold text-[#192D38] dark:text-white">
              Civic Complaints vs Clinical Symptoms (14d)
            </CardTitle>
            <CardDescription className="text-xs text-[#71818A] dark:text-slate-400">
              Dual-stream time series tracking co-occurring intake volume.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 pt-5">
            <TrendChart points={stats?.trend?.points ?? []} />
          </CardContent>
        </Card>

        <Card className="border-[#E4EAE9] bg-white shadow-subtle dark:border-slate-800 dark:bg-[#142B3B]">
          <CardHeader className="border-b border-[#E4EAE9] pb-3 dark:border-slate-800">
            <CardTitle className="text-sm font-bold text-[#192D38] dark:text-white">
              Symptom Urgency Breakdown
            </CardTitle>
            <CardDescription className="text-xs text-[#71818A] dark:text-slate-400">
              Severity distribution of voluntary patient logs.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 pt-5">
            <CategoryPie data={stats?.urgency_reports ?? {}} />
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        <Card className="border-[#E4EAE9] bg-white shadow-subtle dark:border-slate-800 dark:bg-[#142B3B]">
          <CardHeader className="border-b border-[#E4EAE9] pb-3 dark:border-slate-800">
            <CardTitle className="text-sm font-bold text-[#192D38] dark:text-white">
              Top Reported Symptoms (30 Days)
            </CardTitle>
            <CardDescription className="text-xs text-[#71818A] dark:text-slate-400">
              Frequency of extracted clinical keywords from patient reports.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4 pt-5">
            {(stats?.top_symptoms ?? []).length ? (
              <SimpleBarChart
                horizontal
                data={(stats?.top_symptoms ?? []).map((s) => ({
                  name: titleCase(s.symptom),
                  value: s.count,
                }))}
              />
            ) : (
              <p className="text-xs text-[#71818A] text-center py-10">No symptom frequency data compiled yet.</p>
            )}
          </CardContent>
        </Card>

        <Card className="border-[#E4EAE9] bg-white shadow-subtle dark:border-slate-800 dark:bg-[#142B3B]">
          <CardHeader className="border-b border-[#E4EAE9] pb-3 dark:border-slate-800">
            <CardTitle className="text-sm font-bold text-[#192D38] dark:text-white flex items-center gap-2">
              <MapPin className="h-4 w-4 text-[#087F8C]" /> Spatial Health & Civic Distribution (90 Days)
            </CardTitle>
            <CardDescription className="text-xs text-[#71818A] dark:text-slate-400">
              Geolocated cluster density across municipal sectors.
            </CardDescription>
          </CardHeader>
          <CardContent className="p-4">
            <HeatMap points={points} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

/* ---------------------------------- Alerts ---------------------------------- */
function AlertsView({
  alerts,
  statusFilter,
  setStatusFilter,
  onPage,
  onSelect,
  onChanged,
}: {
  alerts: Page<AlertType> | null;
  statusFilter: string;
  setStatusFilter: (v: string) => void;
  onPage: (p: number) => void;
  onSelect: (a: AlertType) => void;
  onChanged: () => void;
}) {
  const { toast } = useToast();
  const [busyId, setBusyId] = React.useState<number | null>(null);

  async function setStatus(alert: AlertType, status: string) {
    setBusyId(alert.id);
    try {
      await api.patch(`/alerts/${alert.id}/status`, { status, note: null });
      toast(`Alert #${alert.id} moved to ${titleCase(status)}`, {
        variant: "success",
        description: status === "CONFIRMED" ? "Field investigation opened automatically" : undefined,
      });
      onChanged();
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
    <div className="space-y-4">
      {/* Filter Header */}
      <div className="flex items-center justify-between border-b border-[#E4EAE9] pb-3 dark:border-slate-800">
        <div className="flex items-center gap-2">
          <span className="text-xs font-semibold text-[#71818A]">Filter Status:</span>
          <select
            className="h-8 rounded-md border border-[#E4EAE9] bg-white px-2.5 text-xs text-[#192D38] dark:border-slate-700 dark:bg-slate-900 dark:text-white"
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
          >
            <option value="">All Alert Statuses</option>
            {["NEW", "REVIEWING", "CONFIRMED", "DISMISSED"].map((s) => (
              <option key={s} value={s}>
                {titleCase(s)}
              </option>
            ))}
          </select>
        </div>
        <span className="text-xs text-[#71818A]">
          {alerts?.total ?? 0} total signal(s) detected
        </span>
      </div>

      {!alerts || alerts.items.length === 0 ? (
        <EmptyState
          title="No alerts matching criteria"
          description="Run a correlation scan to discover cross-domain co-occurrences between complaints and symptoms."
        />
      ) : (
        <div className="space-y-3">
          {alerts.items.map((a) => (
            <Card
              key={a.id}
              className="border-[#E4EAE9] bg-white shadow-subtle dark:border-slate-800 dark:bg-[#142B3B]"
            >
              <CardContent className="p-5">
                <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-3 border-b border-[#E4EAE9]/60 pb-3 dark:border-slate-800">
                  <div className="min-w-0">
                    <div className="flex flex-wrap items-center gap-2 mb-1.5">
                      <span className="font-mono text-xs font-bold text-[#087F8C]">Alert #{a.id}</span>
                      <span
                        className={`rounded px-2 py-0.5 text-[10px] font-semibold border ${
                          a.type === "TEMPORAL_ANOMALY"
                            ? "bg-purple-50 text-purple-800 border-purple-200 dark:bg-purple-950 dark:text-purple-300"
                            : "bg-rose-50 text-rose-800 border-rose-200 dark:bg-rose-950 dark:text-rose-300"
                        }`}
                      >
                        {titleCase(a.type.toLowerCase())}
                      </span>
                      <StatusBadge status={a.status} />
                      <span className="rounded bg-[#F7F8F6] px-2 py-0.5 text-[10px] font-mono font-medium text-[#192D38] border border-[#E4EAE9] dark:bg-slate-800 dark:border-slate-700 dark:text-slate-300">
                        Association: {a.score.toFixed(2)}
                      </span>
                    </div>

                    <h3 className="text-sm font-bold text-[#192D38] dark:text-white leading-tight">
                      {a.title}
                    </h3>

                    <p className="mt-1 text-[11px] text-[#71818A] dark:text-slate-400">
                      {a.n_complaints} complaint(s) · {a.n_reports} health report(s) · {a.n_supporting_pairs} correlated pair(s)
                      {a.districts?.length ? ` · Districts: ${a.districts.join(", ")}` : ""} · {formatDateTime(a.created_at)}
                    </p>
                  </div>
                </div>

                {a.interpretation && (
                  <p className="mt-3 text-xs italic leading-relaxed text-[#71818A] dark:text-slate-300 border-l-2 border-[#087F8C] pl-2.5">
                    {a.interpretation}
                  </p>
                )}

                <div className="mt-4 flex flex-wrap items-center gap-2 pt-1">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => onSelect(a)}
                    className="h-8 text-xs border-[#E4EAE9] hover:bg-[#F7F8F6] dark:border-slate-700"
                  >
                    <Search className="h-3.5 w-3.5 mr-1 text-[#087F8C]" /> Inspect Supporting Evidence
                  </Button>

                  {a.status !== "REVIEWING" && a.status !== "CONFIRMED" && a.status !== "DISMISSED" && (
                    <Button
                      size="sm"
                      variant="outline"
                      loading={busyId === a.id}
                      onClick={() => setStatus(a, "REVIEWING")}
                      className="h-8 text-xs border-[#E4EAE9]"
                    >
                      Begin Review
                    </Button>
                  )}

                  {a.status === "REVIEWING" && (
                    <>
                      <Button
                        size="sm"
                        loading={busyId === a.id}
                        onClick={() => setStatus(a, "CONFIRMED")}
                        className="h-8 bg-[#087F8C] hover:bg-[#066873] text-white text-xs font-semibold px-3"
                      >
                        <CheckCircle2 className="h-3.5 w-3.5 mr-1" /> Confirm + Open Investigation
                      </Button>
                      <Button
                        size="sm"
                        variant="ghost"
                        loading={busyId === a.id}
                        onClick={() => setStatus(a, "DISMISSED")}
                        className="h-8 text-xs text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40"
                      >
                        <XCircle className="h-3.5 w-3.5 mr-1" /> Dismiss
                      </Button>
                    </>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}

          <PaginationBar page={alerts.page} pages={alerts.pages} onPage={onPage} />
        </div>
      )}
    </div>
  );
}

/* ------------------------------- Alert detail ------------------------------- */
function AlertDetail({
  alert,
  onClose,
  onChanged,
}: {
  alert: AlertType;
  onClose: () => void;
  onChanged: () => void;
}) {
  const [note, setNote] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const { toast } = useToast();

  async function changeStatus(status: string) {
    setBusy(true);
    try {
      await api.patch(`/alerts/${alert.id}/status`, { status, note: note || null });
      toast(`Alert #${alert.id} updated to ${titleCase(status.toLowerCase())}`, {
        variant: "success",
      });
      onChanged();
      onClose();
    } catch (err) {
      toast("Status update failed", {
        variant: "error",
        description: err instanceof Error ? err.message : undefined,
      });
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-2xl border-[#E4EAE9] bg-white shadow-elevated dark:border-slate-800 dark:bg-[#142B3B]">
        <DialogHeader className="border-b border-[#E4EAE9] pb-3 dark:border-slate-800">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold text-[#087F8C]">Alert #{alert.id}</span>
            <DialogTitle className="text-base font-bold text-[#192D38] dark:text-white">
              {alert.title}
            </DialogTitle>
          </div>
          <DialogDescription className="text-xs text-[#71818A] dark:text-slate-400">
            Evidence-backed statistical co-occurrence pairs for epidemiological evaluation.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 pt-2 text-xs">
          <EvidencePanel evidence={(alert.evidence ?? null) as AlertEvidence[] | null} />

          {alert.disclaimer && (
            <Alert variant="warning" className="text-xs">
              {alert.disclaimer}
            </Alert>
          )}

          <div className="space-y-1.5 pt-2 border-t border-[#E4EAE9] dark:border-slate-800">
            <Label htmlFor="alert-note" className="text-xs font-semibold text-[#192D38] dark:text-white">
              Official Assessment / Field Note
            </Label>
            <Textarea
              id="alert-note"
              rows={2}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="State rationale for confirmation, assigned health team, or basis for dismissal..."
              className="text-xs border-[#E4EAE9] dark:border-slate-700 dark:bg-slate-900"
            />
          </div>
        </div>

        <DialogFooter className="border-t border-[#E4EAE9] pt-3 dark:border-slate-800 flex justify-end gap-2">
          <Button variant="ghost" size="sm" onClick={() => changeStatus("DISMISSED")} loading={busy} className="text-rose-600">
            Dismiss
          </Button>
          <Button variant="outline" size="sm" onClick={() => changeStatus("REVIEWING")} loading={busy} className="border-[#E4EAE9]">
            Mark Reviewing
          </Button>
          <Button
            size="sm"
            onClick={() => changeStatus("CONFIRMED")}
            loading={busy}
            className="bg-[#087F8C] hover:bg-[#066873] text-white"
          >
            Confirm + Open Field Investigation
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

/* ------------------------------ Investigations ------------------------------ */
function InvestigationsView({
  investigations,
  onChanged,
}: {
  investigations: Page<Investigation> | null;
  onChanged: () => void;
}) {
  const [editing, setEditing] = React.useState<Investigation | null>(null);

  if (!investigations || investigations.items.length === 0) {
    return (
      <EmptyState
        title="No field investigations registered"
        description="Confirm a correlation alert to automatically spawn a field investigation and dispatch ground health teams."
      />
    );
  }

  return (
    <div className="space-y-3">
      {investigations.items.map((inv) => (
        <Card
          key={inv.id}
          className="border-[#E4EAE9] bg-white shadow-subtle dark:border-slate-800 dark:bg-[#142B3B]"
        >
          <CardContent className="p-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#E4EAE9]/60 pb-3 dark:border-slate-800">
              <div>
                <div className="flex items-center gap-2">
                  <span className="font-mono text-xs font-bold text-[#087F8C]">Case #{inv.id}</span>
                  <span className="text-xs text-[#71818A]">· Linked to Alert #{inv.alert_id}</span>
                </div>
                <h3 className="text-sm font-bold text-[#192D38] dark:text-white mt-0.5">{inv.title}</h3>
              </div>
              <div className="flex items-center gap-2">
                <StatusBadge status={inv.status} />
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setEditing(inv)}
                  className="h-8 text-xs border-[#E4EAE9] hover:bg-[#F7F8F6] dark:border-slate-700"
                >
                  Update Status & Findings
                </Button>
              </div>
            </div>

            {inv.notes && (
              <p className="mt-3 text-xs text-[#71818A] dark:text-slate-300">
                <strong className="text-[#192D38] dark:text-white">Field Notes:</strong> {inv.notes}
              </p>
            )}
            {inv.findings && (
              <p className="mt-1 text-xs text-emerald-800 dark:text-emerald-300">
                <strong>Investigation Findings:</strong> {inv.findings}
              </p>
            )}

            <div className="mt-3 border-t border-[#E4EAE9]/40 pt-2 flex items-center justify-between text-[11px] text-[#71818A] dark:text-slate-400">
              <span>Opened {formatDateTime(inv.created_at)}</span>
              {inv.closed_at && <span>Closed {formatDateTime(inv.closed_at)}</span>}
            </div>
          </CardContent>
        </Card>
      ))}

      {editing && (
        <InvestigationDialog
          investigation={editing}
          onClose={() => setEditing(null)}
          onSaved={() => {
            setEditing(null);
            onChanged();
          }}
        />
      )}
    </div>
  );
}

function InvestigationDialog({
  investigation: inv,
  onClose,
  onSaved,
}: {
  investigation: Investigation;
  onClose: () => void;
  onSaved: () => void;
}) {
  const [status, setStatus] = React.useState(inv.status);
  const [notes, setNotes] = React.useState(inv.notes ?? "");
  const [findings, setFindings] = React.useState(inv.findings ?? "");
  const [busy, setBusy] = React.useState(false);
  const { toast } = useToast();

  async function save() {
    setBusy(true);
    try {
      await api.patch(`/investigations/${inv.id}`, {
        status,
        notes: notes || null,
        findings: findings || null,
      });
      toast(`Investigation #${inv.id} updated`, { variant: "success" });
      onSaved();
    } catch (err) {
      toast("Update failed", {
        variant: "error",
        description: err instanceof Error ? err.message : undefined,
      });
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-lg border-[#E4EAE9] bg-white shadow-elevated dark:border-slate-800 dark:bg-[#142B3B]">
        <DialogHeader className="border-b border-[#E4EAE9] pb-3 dark:border-slate-800">
          <DialogTitle className="text-base font-bold text-[#192D38] dark:text-white">
            Update Investigation #{inv.id}
          </DialogTitle>
          <DialogDescription className="text-xs text-[#71818A] dark:text-slate-400">
            Log sampling outcomes, environmental inspection records, and case progression.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-3.5 pt-2 text-xs">
          <div className="space-y-1">
            <Label htmlFor="inv-status" className="text-xs font-semibold text-[#192D38] dark:text-white">
              Investigation Stage
            </Label>
            <Select
              id="inv-status"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="h-9 text-xs border-[#E4EAE9] dark:border-slate-700 dark:bg-slate-900"
            >
              {[
                "OPEN",
                "FIELD_VISIT_SCHEDULED",
                "SAMPLING",
                "CLOSED_RESOLVED",
                "CLOSED_NO_ACTION",
              ].map((s) => (
                <option key={s} value={s}>
                  {titleCase(s.toLowerCase())}
                </option>
              ))}
            </Select>
          </div>

          <div className="space-y-1">
            <Label htmlFor="inv-notes" className="text-xs font-semibold text-[#192D38] dark:text-white">
              Field Team Coordination Notes
            </Label>
            <Textarea
              id="inv-notes"
              rows={3}
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="e.g. Health officers assigned to sector 3 water sampling..."
              className="text-xs border-[#E4EAE9] dark:border-slate-700 dark:bg-slate-900"
            />
          </div>

          <div className="space-y-1">
            <Label htmlFor="inv-findings" className="text-xs font-semibold text-[#192D38] dark:text-white">
              Clinical / Environmental Lab Findings
            </Label>
            <Textarea
              id="inv-findings"
              rows={3}
              value={findings}
              onChange={(e) => setFindings(e.target.value)}
              placeholder="e.g. Water test confirmed E. Coli counts above threshold. Pipeline repair requested."
              className="text-xs border-[#E4EAE9] dark:border-slate-700 dark:bg-slate-900"
            />
          </div>
        </div>

        <DialogFooter className="border-t border-[#E4EAE9] pt-3 dark:border-slate-800 flex justify-end gap-2">
          <Button variant="outline" size="sm" onClick={onClose} className="border-[#E4EAE9]">
            Cancel
          </Button>
          <Button
            size="sm"
            onClick={save}
            loading={busy}
            className="bg-[#087F8C] hover:bg-[#066873] text-white"
          >
            <Syringe className="h-3.5 w-3.5 mr-1" /> Save Investigation Log
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
