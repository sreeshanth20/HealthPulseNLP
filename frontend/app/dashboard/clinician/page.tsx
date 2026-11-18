"use client";

import * as React from "react";
import {
  Activity,
  AlertTriangle,
  BadgeCheck,
  CheckCircle2,
  Clock,
  FileText,
  Filter,
  Loader2,
  MapPin,
  Pill,
  RefreshCw,
  Search,
  Sparkles,
  Stethoscope,
  X,
} from "lucide-react";
import {
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
  UrgencyBadge,
} from "@/components/dashboard-widgets";
import { useToast } from "@/components/ui/toast";
import { api } from "@/lib/api";
import type { MedicalReport, Page } from "@/lib/types";
import { formatDateTime, titleCase, truncate } from "@/lib/utils";

export default function ClinicianDashboard() {
  const [reports, setReports] = React.useState<Page<MedicalReport> | null>(null);
  const [page, setPage] = React.useState(1);
  const [urgency, setUrgency] = React.useState("");
  const [district, setDistrict] = React.useState("");
  const [symptom, setSymptom] = React.useState("");
  const [selected, setSelected] = React.useState<MedicalReport | null>(null);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const [summarizing, setSummarizing] = React.useState(false);
  const { toast } = useToast();

  const load = React.useCallback(async () => {
    setLoading(true);
    try {
      const q = new URLSearchParams({ page: String(page), page_size: "12" });
      if (urgency) q.set("urgency", urgency);
      if (district) q.set("district", district);
      if (symptom) q.set("symptom", symptom);
      setReports(await api.get<Page<MedicalReport>>(`/reports?${q.toString()}`));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load clinical reports");
    } finally {
      setLoading(false);
    }
  }, [page, urgency, district, symptom]);

  React.useEffect(() => {
    load();
  }, [load]);

  async function summarize(report: MedicalReport) {
    setSummarizing(true);
    try {
      const updated = await api.post<MedicalReport>(`/reports/${report.id}/summarize`);
      setSelected(updated);
      toast("Clinical summary regenerated", { variant: "success" });
      load();
    } catch (err) {
      toast("Summarization failed", {
        variant: "error",
        description: err instanceof Error ? err.message : undefined,
      });
    } finally {
      setSummarizing(false);
    }
  }

  const highUrgencyCount =
    reports?.items.filter((r) => ["HIGH", "CRITICAL"].includes(r.urgency)).length ?? 0;

  return (
    <div className="space-y-6">
      {/* Header section */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-[#E4EAE9] pb-5 dark:border-slate-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#192D38] dark:text-white">
            Clinical Surveillance & Triage Review
          </h1>
          <p className="mt-1 text-xs text-[#71818A] dark:text-slate-400">
            De-identified voluntary symptom reports for healthcare professionals. Review extracted medical entities and urgency priority without patient identity leakage.
          </p>
        </div>
        <Button
          variant="outline"
          size="sm"
          onClick={load}
          className="h-8 gap-1.5 border-[#E4EAE9] text-xs hover:bg-[#F7F8F6] dark:border-slate-800 dark:hover:bg-slate-800"
        >
          <RefreshCw className="h-3.5 w-3.5 text-[#087F8C]" /> Refresh Data
        </Button>
      </div>

      {/* Overview Stat Cards */}
      <div className="grid gap-4 sm:grid-cols-3">
        <StatCard
          label="Active Reports in View"
          value={reports?.total ?? "—"}
          hint="Across all monitored districts"
          icon={<Stethoscope className="h-5 w-5" />}
        />
        <StatCard
          label="High / Critical Triage"
          value={highUrgencyCount}
          hint="Requiring immediate clinical observation"
          icon={<AlertTriangle className="h-5 w-5 text-amber-600" />}
        />
        <StatCard
          label="NER Extraction Backend"
          value="Medical NLP"
          hint="Deterministic clinical entity recognizer"
          icon={<Sparkles className="h-5 w-5 text-[#087F8C]" />}
        />
      </div>

      {/* Advanced Filter Bar */}
      <Card className="border-[#E4EAE9] bg-white shadow-subtle dark:border-slate-800 dark:bg-[#142B3B]">
        <CardContent className="p-4">
          <div className="grid gap-3 sm:grid-cols-12 items-end">
            <div className="sm:col-span-5 space-y-1">
              <Label htmlFor="sym" className="text-xs font-semibold text-[#192D38] dark:text-slate-300">
                Search by Symptom Keyword
              </Label>
              <div className="relative">
                <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-[#71818A]" />
                <Input
                  id="sym"
                  placeholder="e.g. diarrhea, vomiting, fever..."
                  value={symptom}
                  onChange={(e) => {
                    setSymptom(e.target.value);
                    setPage(1);
                  }}
                  className="pl-8 h-8 text-xs border-[#E4EAE9] dark:border-slate-700 dark:bg-slate-900"
                />
              </div>
            </div>

            <div className="sm:col-span-3 space-y-1">
              <Label htmlFor="urg" className="text-xs font-semibold text-[#192D38] dark:text-slate-300">
                Urgency Priority
              </Label>
              <Select
                id="urg"
                value={urgency}
                onChange={(e) => {
                  setUrgency(e.target.value);
                  setPage(1);
                }}
                className="h-8 text-xs border-[#E4EAE9] dark:border-slate-700 dark:bg-slate-900"
              >
                <option value="">All Triage Levels</option>
                {["LOW", "MEDIUM", "HIGH", "CRITICAL"].map((u) => (
                  <option key={u} value={u}>
                    {u} Urgency
                  </option>
                ))}
              </Select>
            </div>

            <div className="sm:col-span-4 space-y-1">
              <Label htmlFor="dist" className="text-xs font-semibold text-[#192D38] dark:text-slate-300">
                District / Cluster
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
        </CardContent>
      </Card>

      {/* Reports Feed */}
      {error ? (
        <ErrorState message={error} retry={load} />
      ) : loading ? (
        <LoadingState label="Loading patient symptom surveillance feed…" />
      ) : !reports || reports.items.length === 0 ? (
        <EmptyState
          title="No clinical reports match filter criteria"
          description="Try broadening the urgency filter or searching for another symptom."
        />
      ) : (
        <div className="space-y-4">
          <div className="grid gap-4 lg:grid-cols-2">
            {reports.items.map((r) => (
              <Card
                key={r.id}
                onClick={() => setSelected(r)}
                className="border-[#E4EAE9] bg-white shadow-subtle hover:border-[#087F8C]/60 hover:shadow-card transition-all cursor-pointer dark:border-slate-800 dark:bg-[#142B3B]"
              >
                <CardContent className="p-5 flex flex-col justify-between h-full">
                  <div>
                    <div className="flex items-center justify-between border-b border-[#E4EAE9]/60 pb-3 dark:border-slate-800">
                      <span className="flex items-center gap-2 font-bold text-xs text-[#142B3B] dark:text-white">
                        <FileText className="h-4 w-4 text-[#087F8C]" />
                        {r.patient_alias || "Anonymous Patient"} · #{r.id}
                      </span>
                      <UrgencyBadge urgency={r.urgency} />
                    </div>

                    <p className="mt-3 text-xs leading-relaxed text-[#71818A] dark:text-slate-300">
                      {truncate(r.text, 190)}
                    </p>

                    <div className="mt-3 flex flex-wrap gap-1">
                      {(r.symptoms ?? []).slice(0, 5).map((s) => (
                        <span
                          key={s}
                          className="rounded bg-[#DDF2F0] px-2 py-0.5 text-[10px] font-semibold text-[#087F8C] border border-[#B2E4E0] dark:bg-teal-950 dark:text-teal-300 dark:border-teal-800"
                        >
                          {titleCase(s)}
                        </span>
                      ))}
                      {(r.symptoms ?? []).length > 5 && (
                        <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-[#71818A]">
                          +{(r.symptoms?.length ?? 0) - 5}
                        </span>
                      )}
                    </div>
                  </div>

                  <div className="mt-4 border-t border-[#E4EAE9]/40 pt-2.5 flex items-center justify-between text-[11px] text-[#71818A] dark:text-slate-400">
                    <span>{formatDateTime(r.created_at)}</span>
                    {r.district && (
                      <span className="flex items-center gap-1 font-medium text-[#192D38] dark:text-slate-200">
                        <MapPin className="h-3 w-3 text-[#087F8C]" /> {r.district}
                      </span>
                    )}
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>

          <PaginationBar page={reports.page} pages={reports.pages} onPage={setPage} />
        </div>
      )}

      {/* Clinical Review Detail Dialog */}
      {selected && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-[#142B3B]/60 backdrop-blur-xs p-4"
          onClick={() => setSelected(null)}
        >
          <Card
            className="w-full max-w-2xl max-h-[85vh] overflow-y-auto border-[#E4EAE9] bg-white shadow-elevated dark:border-slate-800 dark:bg-[#142B3B]"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-[#E4EAE9] p-5 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <Stethoscope className="h-4 w-4 text-[#087F8C]" />
                <h2 className="text-base font-bold text-[#192D38] dark:text-white">
                  Report #{selected.id} · {selected.patient_alias || "De-identified Patient"}
                </h2>
              </div>
              <button
                onClick={() => setSelected(null)}
                className="rounded p-1 text-[#71818A] hover:bg-[#F7F8F6] dark:hover:bg-slate-800"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <CardContent className="p-6 space-y-4 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-[#71818A]">Triage Assessment:</span>
                <UrgencyBadge urgency={selected.urgency} />
              </div>

              {/* Patient Narrative */}
              <div className="rounded-md border border-[#E4EAE9] bg-[#F7F8F6] p-4 dark:border-slate-800 dark:bg-slate-900/60">
                <p className="font-semibold text-[#192D38] dark:text-white mb-1">Verbatim Narrative Statement</p>
                <p className="text-[#71818A] dark:text-slate-300 leading-relaxed whitespace-pre-line">
                  {selected.text}
                </p>
              </div>

              {/* Extracted Clinical Entities */}
              <div>
                <p className="text-[11px] font-bold uppercase tracking-wider text-[#71818A] dark:text-slate-400 mb-2 flex items-center gap-1.5">
                  <Pill className="h-3.5 w-3.5 text-[#087F8C]" /> Extracted Clinical Entities ({selected.entity_count ?? 0})
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {(selected.entities ?? []).map((e, i) => {
                    const isSymptom = e.type === "SYMPTOM";
                    const isMed = e.type === "MEDICATION";
                    return (
                      <span
                        key={i}
                        className={`rounded px-2 py-1 text-xs font-medium border ${
                          isSymptom
                            ? "bg-[#DDF2F0] text-[#087F8C] border-[#B2E4E0] dark:bg-teal-950 dark:text-teal-300"
                            : isMed
                            ? "bg-blue-50 text-blue-800 border-blue-200 dark:bg-blue-950 dark:text-blue-300"
                            : "bg-slate-100 text-slate-800 border-slate-200 dark:bg-slate-800 dark:text-slate-300"
                        }`}
                      >
                        {e.text} <span className="text-[10px] opacity-70">· {e.type.toLowerCase()}</span>
                      </span>
                    );
                  })}
                </div>
              </div>

              {/* Triage Reasons */}
              {selected.urgency_reasons && selected.urgency_reasons.length > 0 && (
                <div className="rounded-md border border-[#E4EAE9] p-3 dark:border-slate-800">
                  <p className="font-semibold text-[#192D38] dark:text-white mb-1.5">Urgency Triage Justification</p>
                  <ul className="space-y-1 text-[#71818A] dark:text-slate-400">
                    {selected.urgency_reasons.map((r, i) => (
                      <li key={i} className="flex items-center gap-1.5">
                        <BadgeCheck className="h-3.5 w-3.5 text-[#087F8C] shrink-0" />
                        <span>{r}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Structured digest */}
              {selected.digest && (
                <div className="rounded-md border border-[#E4EAE9] bg-[#F7F8F6] p-3 dark:border-slate-800 dark:bg-slate-900/60">
                  <span className="font-semibold text-[#192D38] dark:text-white">Structured Clinical Digest: </span>
                  <span className="text-[#71818A] dark:text-slate-300">{selected.digest}</span>
                </div>
              )}

              {/* Summary and Regenerate action */}
              <div className="rounded-md border border-[#087F8C]/30 bg-[#DDF2F0]/30 p-4 dark:border-teal-800 dark:bg-teal-950/30">
                <div className="flex items-center justify-between mb-2">
                  <p className="font-bold text-[#142B3B] dark:text-teal-200 flex items-center gap-1.5">
                    <Sparkles className="h-3.5 w-3.5 text-[#087F8C]" /> Extractive AI Summary
                  </p>
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => summarize(selected)}
                    loading={summarizing}
                    className="h-7 text-xs border-[#087F8C]/40 bg-white text-[#087F8C] hover:bg-[#DDF2F0] dark:bg-slate-900"
                  >
                    <RefreshCw className="h-3 w-3 mr-1" /> Regenerate
                  </Button>
                </div>
                <p className="text-xs leading-relaxed text-[#142B3B] dark:text-slate-200">
                  {selected.summary || "No summary compiled yet."}
                </p>
              </div>

              <div className="border-t border-[#E4EAE9] pt-3 flex justify-between text-[#71818A] dark:border-slate-800">
                <span>Logged: {formatDateTime(selected.created_at)}</span>
                {selected.district && <span>Ward: {selected.district}</span>}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
