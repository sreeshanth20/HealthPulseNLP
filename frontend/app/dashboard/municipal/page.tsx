"use client";

import * as React from "react";
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  ChevronRight,
  ClipboardList,
  Clock,
  Copy,
  Filter,
  Layers,
  MapPin,
  RefreshCw,
  Search,
  ShieldAlert,
  Sparkles,
  Users,
  X,
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
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  CategoryBadge,
  EmptyState,
  ErrorState,
  LoadingState,
  PaginationBar,
  StatCard,
  StatusBadge,
  UrgencyBadge,
} from "@/components/dashboard-widgets";
import { HeatMap, type MapPoint } from "@/components/map/heatmap";
import { TrendChart } from "@/components/charts";
import { useToast } from "@/components/ui/toast";
import { api } from "@/lib/api";
import type { Complaint, DashboardStats, Page } from "@/lib/types";
import { formatDateTime, titleCase, truncate } from "@/lib/utils";

const STATUSES = ["SUBMITTED", "ACKNOWLEDGED", "IN_PROGRESS", "RESOLVED", "REJECTED"];
const CATEGORIES = [
  "water_contamination",
  "garbage_sanitation",
  "drainage_sewage",
  "mosquito_menace",
  "road_infrastructure",
  "street_lighting",
  "public_sanitation",
  "noise_pollution",
  "animal_nuisance",
];

export default function MunicipalDashboard() {
  const [stats, setStats] = React.useState<DashboardStats | null>(null);
  const [complaints, setComplaints] = React.useState<Page<Complaint> | null>(null);
  const [points, setPoints] = React.useState<MapPoint[]>([]);
  const [page, setPage] = React.useState(1);
  const [status, setStatus] = React.useState("");
  const [category, setCategory] = React.useState("");
  const [district, setDistrict] = React.useState("");
  const [q, setQ] = React.useState("");
  const [selected, setSelected] = React.useState<Complaint | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const { toast } = useToast();

  const load = React.useCallback(async () => {
    setLoading(true);
    try {
      const qstr = new URLSearchParams({ page: String(page), page_size: "12" });
      if (status) qstr.set("status", status);
      if (category) qstr.set("category", category);
      if (district) qstr.set("district", district);
      if (q) qstr.set("q", q);
      const [overview, list, geo] = await Promise.all([
        api.get<DashboardStats>("/analytics/overview"),
        api.get<Page<Complaint>>(`/complaints?${qstr.toString()}`),
        api.get<{ points: MapPoint[] }>("/complaints/geo?days=90"),
      ]);
      setStats(overview);
      setComplaints(list);
      setPoints(geo.points);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load municipal operations data");
    } finally {
      setLoading(false);
    }
  }, [page, status, category, district, q]);

  React.useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="space-y-6">
      {/* Header section */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-[#E4EAE9] pb-5 dark:border-slate-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#192D38] dark:text-white">
            Municipal Operations & Civic Triaging Command
          </h1>
          <p className="mt-1 text-xs text-[#71818A] dark:text-slate-400">
            Triage, investigate and resolve citizen complaints across urban wards. Duplicate complaints are automatically clustered into incident master records.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={load}
          className="h-8 gap-1.5 border-[#E4EAE9] text-xs hover:bg-[#F7F8F6] dark:border-slate-800"
        >
          <RefreshCw className="h-3.5 w-3.5 text-[#087F8C]" /> Refresh Data
        </Button>
      </div>

      {error ? (
        <ErrorState message={error} retry={load} />
      ) : loading ? (
        <LoadingState label="Synthesizing municipal operations feed…" />
      ) : (
        <>
          {/* Key Metrics */}
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard
              label="Total Complaints"
              value={stats?.total_complaints ?? "—"}
              icon={<ClipboardList className="h-5 w-5" />}
            />
            <StatCard
              label="Active / In Triage"
              value={stats?.open_complaints ?? "—"}
              hint="Submitted + Acknowledged + In Progress"
              icon={<Clock className="h-5 w-5 text-amber-600" />}
            />
            <StatCard
              label="Successfully Resolved"
              value={stats?.resolved_complaints ?? "—"}
              hint="Verified closed after remediation"
              icon={<CheckCircle2 className="h-5 w-5 text-emerald-600" />}
            />
            <StatCard
              label="14-Day Intake Velocity"
              value={stats?.complaints_last_14d ?? "—"}
              hint="Recent reports across all wards"
              icon={<Activity className="h-5 w-5 text-[#087F8C]" />}
            />
          </div>

          {/* Trend Chart Card */}
          <Card className="border-[#E4EAE9] bg-white shadow-subtle dark:border-slate-800 dark:bg-[#142B3B]">
            <CardHeader className="border-b border-[#E4EAE9] pb-3 dark:border-slate-800">
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle className="text-sm font-bold text-[#192D38] dark:text-white">
                    14-Day Cross-Stream Reporting Trend
                  </CardTitle>
                  <CardDescription className="text-xs text-[#71818A] dark:text-slate-400">
                    Comparing civic grievances against voluntary clinical health signals.
                  </CardDescription>
                </div>
                <span className="rounded bg-[#DDF2F0] px-2 py-0.5 text-[10px] font-semibold text-[#087F8C] dark:bg-teal-950 dark:text-teal-300">
                  Daily Co-Occurrence
                </span>
              </div>
            </CardHeader>
            <CardContent className="p-4 pt-5">
              <TrendChart points={stats?.trend?.points ?? []} />
            </CardContent>
          </Card>

          {/* GIS Map & Status Breakdown */}
          <div className="grid gap-6 lg:grid-cols-12 items-start">
            <Card className="lg:col-span-7 border-[#E4EAE9] bg-white shadow-subtle dark:border-slate-800 dark:bg-[#142B3B]">
              <CardHeader className="border-b border-[#E4EAE9] pb-3 dark:border-slate-800">
                <CardTitle className="text-sm font-bold text-[#192D38] dark:text-white flex items-center gap-2">
                  <MapPin className="h-4 w-4 text-[#087F8C]" /> Geospatial Ward Incident Clusters
                </CardTitle>
                <CardDescription className="text-xs text-[#71818A] dark:text-slate-400">
                  Pinpoint markers represent geo-located complaints colored by triage urgency.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-4">
                <HeatMap points={points} />
                <div className="mt-3 flex items-center justify-between text-[11px] text-[#71818A] dark:text-slate-400">
                  <span>Urgency Scale: Green (Low) → Yellow (Med) → Orange (High) → Red (Critical)</span>
                  <span className="font-semibold text-[#192D38] dark:text-slate-200">
                    {points.length} Geocoded Points
                  </span>
                </div>
              </CardContent>
            </Card>

            <Card className="lg:col-span-5 border-[#E4EAE9] bg-white shadow-subtle dark:border-slate-800 dark:bg-[#142B3B]">
              <CardHeader className="border-b border-[#E4EAE9] pb-3 dark:border-slate-800">
                <CardTitle className="text-sm font-bold text-[#192D38] dark:text-white">
                  Workflow Status Distribution
                </CardTitle>
                <CardDescription className="text-xs text-[#71818A] dark:text-slate-400">
                  Current distribution of complaints across lifecycle stages.
                </CardDescription>
              </CardHeader>
              <CardContent className="p-5 space-y-3">
                {Object.entries(stats?.status_breakdown ?? {}).map(([k, v]) => {
                  const total = stats?.total_complaints || 1;
                  const pct = ((v / total) * 100).toFixed(0);
                  return (
                    <div key={k} className="rounded-md border border-[#E4EAE9] p-2.5 dark:border-slate-800">
                      <div className="flex items-center justify-between text-xs mb-1.5">
                        <StatusBadge status={k} />
                        <span className="font-mono text-xs font-semibold text-[#192D38] dark:text-white">
                          {v} <span className="text-[10px] font-normal text-[#71818A]">({pct}%)</span>
                        </span>
                      </div>
                      <div className="h-1.5 w-full overflow-hidden rounded-full bg-[#E4EAE9] dark:bg-slate-800">
                        <div
                          className="h-full rounded-full bg-[#087F8C] transition-all"
                          style={{ width: `${(v / total) * 100}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>
          </div>

          {/* Operations & Triage Table */}
          <Card className="border-[#E4EAE9] bg-white shadow-subtle dark:border-slate-800 dark:bg-[#142B3B]">
            <CardHeader className="border-b border-[#E4EAE9] pb-4 dark:border-slate-800">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                  <CardTitle className="text-sm font-bold text-[#192D38] dark:text-white">
                    Operations Triage & Resolution Table
                  </CardTitle>
                  <CardDescription className="text-xs text-[#71818A] dark:text-slate-400">
                    Filter by status, category, district, or search keywords. Click &apos;Manage Workflow&apos; to change status.
                  </CardDescription>
                </div>
              </div>

              {/* Filters */}
              <div className="grid gap-3 sm:grid-cols-12 items-end pt-3">
                <div className="sm:col-span-4 space-y-1">
                  <Label htmlFor="q" className="text-[11px] font-semibold text-[#71818A]">
                    Search Keyword
                  </Label>
                  <div className="relative">
                    <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-[#71818A]" />
                    <Input
                      id="q"
                      placeholder="Search title, description..."
                      value={q}
                      onChange={(e) => {
                        setQ(e.target.value);
                        setPage(1);
                      }}
                      className="pl-8 h-8 text-xs border-[#E4EAE9] dark:border-slate-700 dark:bg-slate-900"
                    />
                  </div>
                </div>

                <div className="sm:col-span-3 space-y-1">
                  <Label htmlFor="st" className="text-[11px] font-semibold text-[#71818A]">
                    Lifecycle Status
                  </Label>
                  <Select
                    id="st"
                    value={status}
                    onChange={(e) => {
                      setStatus(e.target.value);
                      setPage(1);
                    }}
                    className="h-8 text-xs border-[#E4EAE9] dark:border-slate-700 dark:bg-slate-900"
                  >
                    <option value="">All Statuses</option>
                    {STATUSES.map((s) => (
                      <option key={s} value={s}>
                        {titleCase(s)}
                      </option>
                    ))}
                  </Select>
                </div>

                <div className="sm:col-span-3 space-y-1">
                  <Label htmlFor="cat" className="text-[11px] font-semibold text-[#71818A]">
                    Category
                  </Label>
                  <Select
                    id="cat"
                    value={category}
                    onChange={(e) => {
                      setCategory(e.target.value);
                      setPage(1);
                    }}
                    className="h-8 text-xs border-[#E4EAE9] dark:border-slate-700 dark:bg-slate-900"
                  >
                    <option value="">All Categories</option>
                    {CATEGORIES.map((c) => (
                      <option key={c} value={c}>
                        {titleCase(c)}
                      </option>
                    ))}
                  </Select>
                </div>

                <div className="sm:col-span-2 space-y-1">
                  <Label htmlFor="dist" className="text-[11px] font-semibold text-[#71818A]">
                    District
                  </Label>
                  <Input
                    id="dist"
                    placeholder="e.g. Millbrook"
                    value={district}
                    onChange={(e) => {
                      setDistrict(e.target.value);
                      setPage(1);
                    }}
                    className="h-8 text-xs border-[#E4EAE9] dark:border-slate-700 dark:bg-slate-900"
                  />
                </div>
              </div>
            </CardHeader>

            <CardContent className="p-0">
              {!complaints || complaints.items.length === 0 ? (
                <div className="p-8">
                  <EmptyState title="No complaints match current filters" description="Clear some filters to expand your search." />
                </div>
              ) : (
                <div className="divide-y divide-[#E4EAE9] dark:divide-slate-800">
                  {complaints.items.map((c) => (
                    <div
                      key={c.id}
                      className="p-4 sm:p-5 flex flex-col md:flex-row md:items-center justify-between gap-3 hover:bg-[#F7F8F6]/60 transition-colors dark:hover:bg-slate-900/30"
                    >
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-2 mb-1.5">
                          <span className="font-mono text-xs font-bold text-[#087F8C]">#{c.id}</span>
                          <span className="text-sm font-bold text-[#192D38] dark:text-white">
                            {truncate(c.title, 75)}
                          </span>
                          <CategoryBadge category={c.category} />
                          <UrgencyBadge urgency={c.urgency} />
                          <StatusBadge status={c.status} />
                          {c.duplicate_of_id && (
                            <span className="inline-flex items-center gap-1 rounded bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-700 border border-slate-200 dark:bg-slate-800 dark:text-slate-300">
                              <Copy className="h-3 w-3 text-[#087F8C]" /> Duplicate of #{c.duplicate_of_id}
                            </span>
                          )}
                        </div>

                        <p className="text-xs text-[#71818A] dark:text-slate-300 line-clamp-2">
                          {c.text}
                        </p>

                        <div className="mt-2 flex flex-wrap items-center gap-4 text-[11px] text-[#71818A] dark:text-slate-400">
                          <span>Submitted {formatDateTime(c.created_at)}</span>
                          {c.district && (
                            <span className="flex items-center gap-1 font-medium text-[#192D38] dark:text-slate-200">
                              <MapPin className="h-3 w-3 text-[#087F8C]" /> {c.district}
                            </span>
                          )}
                          {c.resolution_note && (
                            <span className="text-emerald-700 dark:text-emerald-300 font-medium">
                              Note: {c.resolution_note}
                            </span>
                          )}
                        </div>
                      </div>

                      <div className="shrink-0 flex items-center gap-2">
                        <Button
                          size="sm"
                          onClick={() => setSelected(c)}
                          className="h-8 bg-[#087F8C] hover:bg-[#066873] text-white text-xs font-medium px-3"
                        >
                          <Layers className="h-3.5 w-3.5 mr-1" /> Manage Workflow
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <div className="p-4 border-t border-[#E4EAE9] dark:border-slate-800">
                {complaints && (
                  <PaginationBar page={complaints.page} pages={complaints.pages} onPage={setPage} />
                )}
              </div>
            </CardContent>
          </Card>
        </>
      )}

      {/* Workflow Transition Dialog */}
      {selected && (
        <ManageDialog
          complaint={selected}
          onClose={() => setSelected(null)}
          onChanged={() => {
            setSelected(null);
            load();
          }}
        />
      )}
    </div>
  );
}

/* ----------------------------- Manage dialog -------------------------------- */
function ManageDialog({
  complaint: c,
  onClose,
  onChanged,
}: {
  complaint: Complaint;
  onClose: () => void;
  onChanged: () => void;
}) {
  const [next, setNext] = React.useState("");
  const [note, setNote] = React.useState("");
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const { toast } = useToast();

  const allowed =
    {
      SUBMITTED: ["ACKNOWLEDGED", "IN_PROGRESS", "REJECTED"],
      ACKNOWLEDGED: ["IN_PROGRESS", "REJECTED"],
      IN_PROGRESS: ["RESOLVED", "REJECTED"],
      RESOLVED: [],
      REJECTED: [],
    }[c.status] ?? [];

  async function submit() {
    if (!next) return;
    setBusy(true);
    setError(null);
    try {
      await api.patch(`/complaints/${c.id}/status`, { status: next, note: note || null });
      toast(`Complaint #${c.id} updated to ${titleCase(next)}`, { variant: "success" });
      onChanged();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Workflow state transition failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <Dialog open onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-xl border-[#E4EAE9] bg-white shadow-elevated dark:border-slate-800 dark:bg-[#142B3B]">
        <DialogHeader className="border-b border-[#E4EAE9] pb-3 dark:border-slate-800">
          <div className="flex items-center gap-2">
            <span className="font-mono text-xs font-bold text-[#087F8C]">#{c.id}</span>
            <DialogTitle className="text-base font-bold text-[#192D38] dark:text-white">
              {c.title}
            </DialogTitle>
          </div>
          <DialogDescription className="text-xs text-[#71818A] dark:text-slate-400">
            Transition complaint status across municipal resolution workflow.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 text-xs pt-2">
          <div className="flex flex-wrap gap-2">
            <StatusBadge status={c.status} />
            <UrgencyBadge urgency={c.urgency} />
            <CategoryBadge category={c.category} />
            {c.district && (
              <span className="inline-flex items-center gap-1 rounded border border-[#E4EAE9] bg-[#F7F8F6] px-2 py-0.5 text-xs text-[#192D38] dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200">
                <MapPin className="h-3 w-3 text-[#087F8C]" /> {c.district}
              </span>
            )}
          </div>

          <div className="rounded-md border border-[#E4EAE9] bg-[#F7F8F6] p-3 text-xs leading-relaxed text-[#192D38] dark:border-slate-800 dark:bg-slate-900/60 dark:text-slate-300">
            {c.text}
          </div>

          {c.resolution_note && (
            <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-xs dark:border-slate-800 dark:bg-slate-900">
              <span className="font-semibold text-[#192D38] dark:text-white">Previous Note:</span>{" "}
              <span className="text-[#71818A] dark:text-slate-300">{c.resolution_note}</span>
            </div>
          )}

          {allowed.length === 0 ? (
            <div className="rounded-md border border-slate-200 bg-slate-50 p-3 text-center text-xs text-[#71818A] dark:border-slate-800 dark:bg-slate-900">
              This grievance has reached a terminal state ({titleCase(c.status)}).
            </div>
          ) : (
            <div className="space-y-3 rounded-lg border border-[#E4EAE9] p-4 dark:border-slate-800">
              <p className="font-semibold text-xs text-[#192D38] dark:text-white">Workflow Action</p>
              <div className="space-y-1">
                <Label htmlFor="next-status" className="text-xs text-[#71818A]">
                  New Resolution Status
                </Label>
                <Select
                  id="next-status"
                  value={next}
                  onChange={(e) => setNext(e.target.value)}
                  className="h-9 text-xs border-[#E4EAE9] dark:border-slate-700 dark:bg-slate-900"
                >
                  <option value="">Select target status…</option>
                  {allowed.map((s) => (
                    <option key={s} value={s}>
                      Move to {titleCase(s)}
                    </option>
                  ))}
                </Select>
              </div>

              <div className="space-y-1">
                <Label htmlFor="res-note" className="text-xs text-[#71818A]">
                  Remediation Note / Action Log (optional)
                </Label>
                <Input
                  id="res-note"
                  value={note}
                  onChange={(e) => setNote(e.target.value)}
                  placeholder="e.g. Field inspection completed, valve replaced, water sample sent for culture"
                  className="h-9 text-xs border-[#E4EAE9] dark:border-slate-700 dark:bg-slate-900"
                />
              </div>

              {error && <Alert variant="destructive" className="text-xs">{error}</Alert>}
            </div>
          )}
        </div>

        <DialogFooter className="border-t border-[#E4EAE9] pt-3 dark:border-slate-800 flex justify-end gap-2">
          <Button variant="outline" size="sm" onClick={onClose} className="border-[#E4EAE9]">
            Cancel
          </Button>
          {allowed.length > 0 && (
            <Button
              size="sm"
              onClick={submit}
              loading={busy}
              disabled={!next}
              className="bg-[#087F8C] hover:bg-[#066873] text-white"
            >
              <CheckCircle2 className="h-3.5 w-3.5 mr-1.5" /> Confirm Transition
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
