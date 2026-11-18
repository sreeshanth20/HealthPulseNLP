"use client";

import * as React from "react";
import {
  Activity,
  AlertCircle,
  BadgeCheck,
  BrainCircuit,
  CheckCircle2,
  ChevronRight,
  Clock,
  Copy,
  FileText,
  FileUp,
  Filter,
  Info,
  Loader2,
  MapPin,
  Megaphone,
  PlusCircle,
  Search,
  Send,
  Sparkles,
  TriangleAlert,
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
  ProgressBar,
  Separator,
  Textarea,
} from "@/components/ui/core";
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
import { useToast } from "@/components/ui/toast";
import { api } from "@/lib/api";
import type { Complaint, ComplaintAnalysis, DuplicateCandidate, Page } from "@/lib/types";
import { formatDateTime, titleCase, truncate } from "@/lib/utils";

interface CreateResponse {
  complaint: Complaint;
  analysis: ComplaintAnalysis;
  duplicate_candidates: DuplicateCandidate[];
  duplicate_detected: boolean;
}

const DEMO_DISTRICTS = ["Millbrook", "Oldtown", "Riverside", "Hillside", "Harbor", "Central Ward"];

export default function CitizenDashboard() {
  const { toast } = useToast();
  const [tab, setTab] = React.useState<"new" | "mine">("new");
  const [refreshTrigger, setRefreshTrigger] = React.useState(0);

  return (
    <div className="space-y-6">
      {/* Header section */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-[#E4EAE9] pb-5 dark:border-slate-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#192D38] dark:text-white">
            Civic Grievance & Environmental Center
          </h1>
          <p className="mt-1 text-xs text-[#71818A] dark:text-slate-400">
            Submit localized environmental complaints. On-device NLP classifies severity, geocodes locations, and flags duplicate reports.
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex items-center gap-1.5 rounded-lg border border-[#E4EAE9] bg-white p-1 shadow-subtle dark:border-slate-800 dark:bg-slate-900">
          <button
            onClick={() => setTab("new")}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold transition-colors ${
              tab === "new"
                ? "bg-[#087F8C] text-white shadow-xs"
                : "text-[#71818A] hover:text-[#192D38] dark:hover:text-white"
            }`}
          >
            <PlusCircle className="h-3.5 w-3.5" /> File New Report
          </button>
          <button
            onClick={() => setTab("mine")}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold transition-colors ${
              tab === "mine"
                ? "bg-[#087F8C] text-white shadow-xs"
                : "text-[#71818A] hover:text-[#192D38] dark:hover:text-white"
            }`}
          >
            <Megaphone className="h-3.5 w-3.5" /> My History
          </button>
        </div>
      </div>

      {tab === "new" ? (
        <NewComplaintForm
          toast={toast}
          onCreated={() => {
            setTab("mine");
            setRefreshTrigger((prev) => prev + 1);
          }}
        />
      ) : (
        <MyComplaints key={refreshTrigger} />
      )}
    </div>
  );
}

/* ------------------------------- New complaint ------------------------------ */
function NewComplaintForm({
  toast,
  onCreated,
}: {
  toast: ReturnType<typeof useToast>["toast"];
  onCreated: () => void;
}) {
  const [title, setTitle] = React.useState("");
  const [text, setText] = React.useState("");
  const [address, setAddress] = React.useState("");
  const [lat, setLat] = React.useState("");
  const [lng, setLng] = React.useState("");
  const [analysis, setAnalysis] = React.useState<ComplaintAnalysis | null>(null);
  const [analyzing, setAnalyzing] = React.useState(false);
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const analyzeTimer = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  // Live NLP preview
  async function analyzePreview(value: string) {
    if (value.trim().length < 15) {
      setAnalysis(null);
      return;
    }
    setAnalyzing(true);
    try {
      const result = await api.post<ComplaintAnalysis>("/intelligence/preview", {
        text: value,
        lat: lat ? Number(lat) : null,
        lng: lng ? Number(lng) : null,
      });
      setAnalysis(result);
    } catch {
      /* preview best effort */
    } finally {
      setAnalyzing(false);
    }
  }

  function onTextChange(value: string) {
    setText(value);
    if (analyzeTimer.current) clearTimeout(analyzeTimer.current);
    analyzeTimer.current = setTimeout(() => analyzePreview(value), 600);
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const body = {
        title: title.trim(),
        text: text.trim(),
        address: address.trim() || null,
        lat: lat ? Number(lat) : null,
        lng: lng ? Number(lng) : null,
      };
      const result = await api.post<CreateResponse>("/complaints", body);
      toast(
        result.duplicate_detected
          ? "Grievance submitted — duplicate pattern detected"
          : "Grievance submitted successfully",
        {
          variant: result.duplicate_detected ? "info" : "success",
          description: `Classified as ${titleCase(result.analysis.category)} · Triage ${result.analysis.urgency.label}`,
        }
      );
      setTitle("");
      setText("");
      setAddress("");
      setLat("");
      setLng("");
      setAnalysis(null);
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to submit grievance");
    } finally {
      setSubmitting(false);
    }
  }

  function applyQuickSample(t: string, desc: string, d: string) {
    setTitle(t);
    setText(desc);
    setAddress(d);
    analyzePreview(desc);
  }

  return (
    <div className="grid gap-6 lg:grid-cols-12 items-start">
      {/* Main submission form */}
      <Card className="lg:col-span-7 border-[#E4EAE9] bg-white shadow-subtle dark:border-slate-800 dark:bg-[#142B3B]">
        <CardHeader className="border-b border-[#E4EAE9] pb-4 dark:border-slate-800">
          <CardTitle className="text-base font-bold text-[#192D38] dark:text-white">
            Incident Description & Location
          </CardTitle>
          <CardDescription className="text-xs text-[#71818A] dark:text-slate-400">
            Provide details regarding the civic or environmental anomaly (e.g. water contamination, sewage overflow, pesticide drift, dead birds, or chemical stench).
          </CardDescription>
        </CardHeader>
        <CardContent className="p-6 space-y-4">
          {error && <Alert variant="destructive" className="text-xs">{error}</Alert>}

          {/* Quick template chips */}
          <div className="rounded-md border border-[#E4EAE9] bg-[#F7F8F6] p-3 dark:border-slate-800 dark:bg-slate-900/60">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-[#71818A] dark:text-slate-400 flex items-center gap-1 mb-2">
              <Sparkles className="h-3 w-3 text-[#087F8C]" /> Sample Incident Scenarios
            </span>
            <div className="flex flex-wrap gap-1.5">
              <button
                type="button"
                onClick={() =>
                  applyQuickSample(
                    "Sewage odor in drinking water near Millbrook Market",
                    "The community tap water in Millbrook ward 3 has been smelling like raw sewage for 3 days. Tap water is discolored and neighbors report nausea.",
                    "Millbrook Market, Ward 3"
                  )
                }
                className="rounded border border-[#E4EAE9] bg-white px-2 py-1 text-[11px] font-medium text-[#192D38] hover:border-[#087F8C] hover:text-[#087F8C] dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
              >
                Water Contamination
              </button>
              <button
                type="button"
                onClick={() =>
                  applyQuickSample(
                    "Stagnant drainage and mosquito breeding near Riverside school",
                    "Heavy stagnant dirty water overflowing from open municipal drain right outside the school gate. Severe mosquito infestation and stench.",
                    "Riverside North Avenue"
                  )
                }
                className="rounded border border-[#E4EAE9] bg-white px-2 py-1 text-[11px] font-medium text-[#192D38] hover:border-[#087F8C] hover:text-[#087F8C] dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
              >
                Drainage Overflow
              </button>
              <button
                type="button"
                onClick={() =>
                  applyQuickSample(
                    "Dead crows and birds found near Hillside park",
                    "Found four dead birds and crows within 50 meters near Hillside municipal park walking trail with no visible physical trauma.",
                    "Hillside Park Trail"
                  )
                }
                className="rounded border border-[#E4EAE9] bg-white px-2 py-1 text-[11px] font-medium text-[#192D38] hover:border-[#087F8C] hover:text-[#087F8C] dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
              >
                Animal Mortality / Pests
              </button>
            </div>
          </div>

          <form onSubmit={submit} className="space-y-4">
            <div className="space-y-1">
              <Label htmlFor="title" className="text-xs font-semibold text-[#192D38] dark:text-slate-300">
                Grievance Title
              </Label>
              <Input
                id="title"
                required
                minLength={5}
                maxLength={200}
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Sewage contamination in piped water supply"
                className="h-9 border-[#E4EAE9] text-xs focus-visible:ring-[#087F8C] dark:border-slate-700 dark:bg-slate-900"
              />
            </div>

            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <Label htmlFor="text" className="text-xs font-semibold text-[#192D38] dark:text-slate-300 flex items-center gap-2">
                  Detailed Incident Narrative
                  {analyzing && <Loader2 className="h-3 w-3 animate-spin text-[#087F8C]" />}
                </Label>
                <span className="text-[11px] text-[#71818A]">{text.length} chars</span>
              </div>
              <Textarea
                id="text"
                required
                minLength={15}
                maxLength={6000}
                rows={5}
                value={text}
                onChange={(e) => onTextChange(e.target.value)}
                placeholder="Describe what is occurring, visual evidence (color, smell, density), how many residences are affected, and known timeline..."
                className="border-[#E4EAE9] text-xs focus-visible:ring-[#087F8C] dark:border-slate-700 dark:bg-slate-900"
              />
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              <div className="space-y-1 sm:col-span-3">
                <Label htmlFor="address" className="text-xs font-semibold text-[#192D38] dark:text-slate-300">
                  District, Street or Landmark
                </Label>
                <Input
                  id="address"
                  value={address}
                  onChange={(e) => setAddress(e.target.value)}
                  placeholder="e.g. Millbrook Market, Sector 4"
                  className="h-9 border-[#E4EAE9] text-xs focus-visible:ring-[#087F8C] dark:border-slate-700 dark:bg-slate-900"
                />
              </div>

              <div className="space-y-1">
                <Label htmlFor="lat" className="text-[11px] font-medium text-[#71818A] dark:text-slate-400">
                  Latitude (opt)
                </Label>
                <Input
                  id="lat"
                  inputMode="decimal"
                  placeholder="17.6965"
                  value={lat}
                  onChange={(e) => setLat(e.target.value)}
                  className="h-8 text-xs border-[#E4EAE9] dark:border-slate-700 dark:bg-slate-900"
                />
              </div>

              <div className="space-y-1">
                <Label htmlFor="lng" className="text-[11px] font-medium text-[#71818A] dark:text-slate-400">
                  Longitude (opt)
                </Label>
                <Input
                  id="lng"
                  inputMode="decimal"
                  placeholder="83.2208"
                  value={lng}
                  onChange={(e) => setLng(e.target.value)}
                  className="h-8 text-xs border-[#E4EAE9] dark:border-slate-700 dark:bg-slate-900"
                />
              </div>

              <div className="flex items-end">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    setLat("17.6965");
                    setLng("83.2208");
                  }}
                  className="h-8 w-full text-[11px] border-[#E4EAE9] dark:border-slate-700"
                >
                  <MapPin className="h-3 w-3 mr-1 text-[#087F8C]" /> Fill Demo GPS
                </Button>
              </div>
            </div>

            <Button
              type="submit"
              loading={submitting}
              className="w-full sm:w-auto h-9 bg-[#087F8C] hover:bg-[#066873] text-white font-medium text-xs px-5 shadow-sm"
            >
              <Send className="h-3.5 w-3.5 mr-1.5" /> Submit Grievance
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Real-time NLP Triage Inspector */}
      <Card className="lg:col-span-5 border-[#E4EAE9] bg-white shadow-subtle dark:border-slate-800 dark:bg-[#142B3B]">
        <CardHeader className="border-b border-[#E4EAE9] pb-4 dark:border-slate-800">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-bold text-[#192D38] dark:text-white flex items-center gap-2">
              <BrainCircuit className="h-4 w-4 text-[#087F8C]" /> Real-Time NLP Triage
            </CardTitle>
            <span className="rounded bg-[#DDF2F0] px-2 py-0.5 text-[10px] font-semibold text-[#087F8C] dark:bg-teal-950 dark:text-teal-300">
              Live Classifier
            </span>
          </div>
          <CardDescription className="text-xs text-[#71818A] dark:text-slate-400">
            Evaluates category classification confidence, urgency scoring, and geocoded location.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-5">
          {!analysis ? (
            <div className="rounded-lg border border-dashed border-[#E4EAE9] p-8 text-center dark:border-slate-800">
              <Activity className="h-8 w-8 mx-auto text-[#71818A] opacity-40 mb-2" />
              <p className="text-xs font-semibold text-[#192D38] dark:text-white">Awaiting Narrative Input</p>
              <p className="mt-1 text-[11px] text-[#71818A] dark:text-slate-400 max-w-xs mx-auto">
                Type at least 15 characters into the description box to activate on-device NLP triage.
              </p>
            </div>
          ) : (
            <div className="space-y-4 text-xs">
              {/* Category */}
              <div className="rounded-lg border border-[#E4EAE9] bg-[#F7F8F6] p-3 dark:border-slate-800 dark:bg-slate-900/60">
                <div className="flex items-center justify-between mb-1.5">
                  <span className="font-semibold text-[#192D38] dark:text-white">Predicted Category</span>
                  <CategoryBadge category={analysis.category} />
                </div>
                <div className="flex items-center justify-between text-[11px] text-[#71818A] dark:text-slate-400 mb-1">
                  <span>Confidence Level</span>
                  <span className="font-mono font-semibold text-[#087F8C]">
                    {(analysis.category_confidence * 100).toFixed(1)}%
                  </span>
                </div>
                <ProgressBar value={analysis.category_confidence} className="h-1.5 bg-[#E4EAE9]" />
              </div>

              {/* Urgency */}
              <div className="rounded-lg border border-[#E4EAE9] bg-[#F7F8F6] p-3 dark:border-slate-800 dark:bg-slate-900/60">
                <div className="flex items-center justify-between">
                  <span className="font-semibold text-[#192D38] dark:text-white">Urgency Assessment</span>
                  <UrgencyBadge urgency={analysis.urgency.label} />
                </div>
                {analysis.urgency.reasons.length > 0 && (
                  <ul className="mt-2 space-y-1 text-[11px] text-[#71818A] dark:text-slate-400">
                    {analysis.urgency.reasons.map((r) => (
                      <li key={r} className="flex items-start gap-1.5">
                        <BadgeCheck className="h-3 w-3 text-[#087F8C] shrink-0 mt-0.5" />
                        <span>{r}</span>
                      </li>
                    ))}
                  </ul>
                )}
              </div>

              {/* Location & Language */}
              <div className="grid grid-cols-2 gap-2">
                <div className="rounded-lg border border-[#E4EAE9] bg-[#F7F8F6] p-2.5 dark:border-slate-800 dark:bg-slate-900/60">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-[#71818A] dark:text-slate-400">
                    Extracted Ward
                  </p>
                  <p className="mt-1 font-semibold text-[#192D38] dark:text-white flex items-center gap-1">
                    <MapPin className="h-3 w-3 text-[#087F8C]" />
                    {analysis.location.district || "City-wide"}
                  </p>
                </div>
                <div className="rounded-lg border border-[#E4EAE9] bg-[#F7F8F6] p-2.5 dark:border-slate-800 dark:bg-slate-900/60">
                  <p className="text-[10px] font-semibold uppercase tracking-wider text-[#71818A] dark:text-slate-400">
                    Detected Language
                  </p>
                  <p className="mt-1 font-semibold text-[#192D38] dark:text-white">
                    {analysis.language?.toUpperCase() || "EN"}
                  </p>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

/* ------------------------------ My complaints ------------------------------- */
function MyComplaints() {
  const [page, setPage] = React.useState(1);
  const [status, setStatus] = React.useState("");
  const [searchTerm, setSearchTerm] = React.useState("");
  const [selectedComplaint, setSelectedComplaint] = React.useState<Complaint | null>(null);
  const [data, setData] = React.useState<Page<Complaint> | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(true);

  const load = React.useCallback(async () => {
    setLoading(true);
    try {
      const query = new URLSearchParams({ page: String(page), page_size: "10" });
      if (status) query.set("status", status);
      if (searchTerm.trim()) query.set("q", searchTerm.trim());
      setData(await api.get<Page<Complaint>>(`/complaints?${query.toString()}`));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load submitted complaints");
    } finally {
      setLoading(false);
    }
  }, [page, status, searchTerm]);

  React.useEffect(() => {
    load();
  }, [load]);

  const openCount = data?.items.filter((c) => !["RESOLVED", "REJECTED"].includes(c.status)).length ?? 0;
  const duplicateCount = data?.items.filter((c) => c.duplicate_of_id).length ?? 0;

  return (
    <div className="space-y-5">
      {/* Metrics Row */}
      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard
          label="Total Submitted"
          value={data?.total ?? "—"}
          hint="Tracked civic reports"
          icon={<Megaphone className="h-5 w-5" />}
        />
        <StatCard
          label="Active / Under Triage"
          value={openCount}
          hint="Action or investigation pending"
          icon={<Clock className="h-5 w-5 text-amber-600" />}
        />
        <StatCard
          label="Duplicate Clustered"
          value={duplicateCount}
          hint="Linked to community incident master"
          icon={<Copy className="h-5 w-5 text-[#087F8C]" />}
        />
      </div>

      {/* Filter and Search Bar */}
      <Card className="border-[#E4EAE9] bg-white shadow-subtle dark:border-slate-800 dark:bg-[#142B3B]">
        <CardContent className="p-3.5 flex flex-col sm:flex-row gap-3 items-center justify-between">
          <div className="relative w-full sm:w-72">
            <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-[#71818A]" />
            <Input
              placeholder="Search complaints..."
              value={searchTerm}
              onChange={(e) => {
                setSearchTerm(e.target.value);
                setPage(1);
              }}
              className="pl-8 h-8 text-xs border-[#E4EAE9] dark:border-slate-700 dark:bg-slate-900"
            />
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <span className="text-xs text-[#71818A] whitespace-nowrap">Filter Status:</span>
            <select
              className="h-8 rounded-md border border-[#E4EAE9] bg-white px-2.5 text-xs text-[#192D38] dark:border-slate-700 dark:bg-slate-900 dark:text-white"
              value={status}
              onChange={(e) => {
                setStatus(e.target.value);
                setPage(1);
              }}
            >
              <option value="">All Statuses</option>
              {["SUBMITTED", "ACKNOWLEDGED", "IN_PROGRESS", "RESOLVED", "REJECTED"].map((s) => (
                <option key={s} value={s}>
                  {titleCase(s)}
                </option>
              ))}
            </select>
          </div>
        </CardContent>
      </Card>

      {/* List Content */}
      {error ? (
        <ErrorState message={error} retry={load} />
      ) : loading ? (
        <LoadingState label="Retrieving your submitted grievances…" />
      ) : !data || data.items.length === 0 ? (
        <EmptyState
          title="No grievances recorded"
          description="You haven't submitted any civic complaints yet. Switch to 'File New Report' to report an issue."
        />
      ) : (
        <div className="space-y-3">
          {data.items.map((c) => (
            <Card
              key={c.id}
              onClick={() => setSelectedComplaint(c)}
              className="border-[#E4EAE9] bg-white shadow-subtle hover:border-[#087F8C]/60 hover:shadow-card transition-all cursor-pointer dark:border-slate-800 dark:bg-[#142B3B]"
            >
              <CardContent className="p-4 sm:p-5">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#E4EAE9]/60 pb-3 dark:border-slate-800">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-xs font-bold text-[#087F8C]">#{c.id}</span>
                    <h3 className="text-sm font-bold text-[#192D38] dark:text-white">{c.title}</h3>
                    {c.duplicate_of_id && (
                      <span className="rounded bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-700 border border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700">
                        Duplicate of #{c.duplicate_of_id}
                      </span>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <CategoryBadge category={c.category} />
                    <UrgencyBadge urgency={c.urgency} />
                    <StatusBadge status={c.status} />
                  </div>
                </div>

                <p className="mt-3 text-xs leading-relaxed text-[#71818A] dark:text-slate-300">
                  {truncate(c.text, 240)}
                </p>

                <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-[11px] text-[#71818A] dark:text-slate-400 border-t border-[#E4EAE9]/40 pt-2.5">
                  <div className="flex items-center gap-3">
                    <span>Submitted {formatDateTime(c.created_at)}</span>
                    {c.district && (
                      <span className="flex items-center gap-1 font-medium text-[#192D38] dark:text-slate-200">
                        <MapPin className="h-3 w-3 text-[#087F8C]" /> {c.district}
                      </span>
                    )}
                  </div>
                  {c.resolution_note && (
                    <span className="text-emerald-700 dark:text-emerald-300 font-medium truncate max-w-xs">
                      Resolution: {c.resolution_note}
                    </span>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}

          <PaginationBar page={data.page} pages={data.pages} onPage={setPage} />
        </div>
      )}

      {/* Detail Modal */}
      {selectedComplaint && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-[#142B3B]/60 backdrop-blur-xs p-4"
          onClick={() => setSelectedComplaint(null)}
        >
          <Card
            className="w-full max-w-xl max-h-[85vh] overflow-y-auto border-[#E4EAE9] bg-white shadow-elevated dark:border-slate-800 dark:bg-[#142B3B]"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-[#E4EAE9] p-5 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <span className="font-mono text-xs font-bold text-[#087F8C]">#{selectedComplaint.id}</span>
                <h2 className="text-base font-bold text-[#192D38] dark:text-white">{selectedComplaint.title}</h2>
              </div>
              <button
                onClick={() => setSelectedComplaint(null)}
                className="rounded p-1 text-[#71818A] hover:bg-[#F7F8F6] dark:hover:bg-slate-800"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <CardContent className="p-6 space-y-4 text-xs">
              <div className="flex flex-wrap gap-2">
                <StatusBadge status={selectedComplaint.status} />
                <UrgencyBadge urgency={selectedComplaint.urgency} />
                <CategoryBadge category={selectedComplaint.category} />
              </div>

              <div className="rounded-md border border-[#E4EAE9] bg-[#F7F8F6] p-3 dark:border-slate-800 dark:bg-slate-900/60">
                <p className="font-semibold text-[#192D38] dark:text-white mb-1">Full Incident Statement</p>
                <p className="text-[#71818A] dark:text-slate-300 leading-relaxed whitespace-pre-line">
                  {selectedComplaint.text}
                </p>
              </div>

              {selectedComplaint.urgency_reasons && selectedComplaint.urgency_reasons.length > 0 && (
                <div>
                  <p className="font-semibold text-[#192D38] dark:text-white mb-1">Triage Rationale</p>
                  <ul className="space-y-1 text-[#71818A] dark:text-slate-300">
                    {selectedComplaint.urgency_reasons.map((r, i) => (
                      <li key={i} className="flex items-center gap-1.5">
                        <BadgeCheck className="h-3 w-3 text-[#087F8C]" /> {r}
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {selectedComplaint.resolution_note && (
                <div className="rounded-md border border-emerald-200 bg-emerald-50/60 p-3 text-emerald-900 dark:border-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-200">
                  <p className="font-bold">Official Resolution Note</p>
                  <p className="mt-1">{selectedComplaint.resolution_note}</p>
                </div>
              )}

              <div className="border-t border-[#E4EAE9] pt-3 flex justify-between text-[#71818A] dark:border-slate-800">
                <span>Submitted: {formatDateTime(selectedComplaint.created_at)}</span>
                {selectedComplaint.resolved_at && (
                  <span>Resolved: {formatDateTime(selectedComplaint.resolved_at)}</span>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
