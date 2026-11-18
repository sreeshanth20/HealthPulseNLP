"use client";

import * as React from "react";
import {
  Activity,
  AlertCircle,
  BadgeCheck,
  BrainCircuit,
  Calendar,
  CheckCircle2,
  Clock,
  Download,
  Eye,
  FileCheck2,
  FileText,
  FileUp,
  HeartPulse,
  Info,
  Loader2,
  MapPin,
  Pill,
  PlusCircle,
  Send,
  Sparkles,
  Stethoscope,
  Trash2,
  Upload,
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
  EmptyState,
  ErrorState,
  LoadingState,
  StatCard,
  UrgencyBadge,
} from "@/components/dashboard-widgets";
import { useToast } from "@/components/ui/toast";
import { api } from "@/lib/api";
import type { DocumentMeta, MedicalReport } from "@/lib/types";
import { formatDateTime, titleCase, truncate } from "@/lib/utils";

export default function PatientDashboard() {
  const [tab, setTab] = React.useState<"new" | "reports" | "documents">("new");
  const [refreshTrigger, setRefreshTrigger] = React.useState(0);

  return (
    <div className="space-y-6">
      {/* Header section */}
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between border-b border-[#E4EAE9] pb-5 dark:border-slate-800">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-[#192D38] dark:text-white">
            Patient Health & Voluntary Clinical Portal
          </h1>
          <p className="mt-1 text-xs text-[#71818A] dark:text-slate-400">
            Log health symptoms in natural language and upload clinical documents. Only de-identified data is shared with public health epidemiologists.
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
            <PlusCircle className="h-3.5 w-3.5" /> Log Symptoms
          </button>
          <button
            onClick={() => setTab("reports")}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold transition-colors ${
              tab === "reports"
                ? "bg-[#087F8C] text-white shadow-xs"
                : "text-[#71818A] hover:text-[#192D38] dark:hover:text-white"
            }`}
          >
            <HeartPulse className="h-3.5 w-3.5" /> My History
          </button>
          <button
            onClick={() => setTab("documents")}
            className={`flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-semibold transition-colors ${
              tab === "documents"
                ? "bg-[#087F8C] text-white shadow-xs"
                : "text-[#71818A] hover:text-[#192D38] dark:hover:text-white"
            }`}
          >
            <FileText className="h-3.5 w-3.5" /> Clinical Vault
          </button>
        </div>
      </div>

      {tab === "new" && (
        <NewReportForm
          onCreated={() => {
            setTab("reports");
            setRefreshTrigger((prev) => prev + 1);
          }}
        />
      )}
      {tab === "reports" && <MyReports key={refreshTrigger} />}
      {tab === "documents" && (
        <MyDocuments
          onReportGenerated={() => {
            setTab("reports");
            setRefreshTrigger((prev) => prev + 1);
          }}
        />
      )}
    </div>
  );
}

/* ------------------------------- New report --------------------------------- */
function NewReportForm({ onCreated }: { onCreated: () => void }) {
  const { toast } = useToast();
  const [text, setText] = React.useState("");
  const [district, setDistrict] = React.useState("");
  const [lat, setLat] = React.useState("");
  const [lng, setLng] = React.useState("");
  const [analysis, setAnalysis] = React.useState<MedicalReport | null>(null);
  const [analyzing, setAnalyzing] = React.useState(false);
  const [submitting, setSubmitting] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);
  const timer = React.useRef<ReturnType<typeof setTimeout> | null>(null);

  async function preview(value: string) {
    if (value.trim().length < 15) {
      setAnalysis(null);
      return;
    }
    setAnalyzing(true);
    try {
      const out = await api.post<{
        entities: { text: string; type: string; canonical: string }[];
        symptoms: string[];
        urgency: { label: string; score: number; reasons: string[] };
        summary: string;
        digest: string;
        symptom_categories: string[];
      }>("/intelligence/preview-report", { text: value });
      setAnalysis(out as unknown as MedicalReport);
    } catch {
      /* best effort */
    } finally {
      setAnalyzing(false);
    }
  }

  function onTextChange(value: string) {
    setText(value);
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => preview(value), 600);
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const created = await api.post<MedicalReport>("/reports", {
        text: text.trim(),
        district: district.trim() || null,
        lat: lat ? Number(lat) : null,
        lng: lng ? Number(lng) : null,
      });
      toast("Health report recorded", {
        variant: "success",
        description: `Triage ${created.urgency} · ${created.entity_count} clinical entities recognized`,
      });
      setText("");
      setDistrict("");
      setLat("");
      setLng("");
      setAnalysis(null);
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Submission failed");
    } finally {
      setSubmitting(false);
    }
  }

  function applySample(sampleText: string, sampleDist: string) {
    setText(sampleText);
    setDistrict(sampleDist);
    preview(sampleText);
  }

  return (
    <div className="grid gap-6 lg:grid-cols-12 items-start">
      {/* Form Card */}
      <Card className="lg:col-span-7 border-[#E4EAE9] bg-white shadow-subtle dark:border-slate-800 dark:bg-[#142B3B]">
        <CardHeader className="border-b border-[#E4EAE9] pb-4 dark:border-slate-800">
          <CardTitle className="text-base font-bold text-[#192D38] dark:text-white">
            Log Clinical Symptoms
          </CardTitle>
          <CardDescription className="text-xs text-[#71818A] dark:text-slate-400">
            Describe symptoms experienced by you or family members. Mention onset duration, temperature, gastrointestinal or respiratory signs.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-6 space-y-4">
          {error && <Alert variant="destructive" className="text-xs">{error}</Alert>}

          {/* Preset templates */}
          <div className="rounded-md border border-[#E4EAE9] bg-[#F7F8F6] p-3 dark:border-slate-800 dark:bg-slate-900/60">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-[#71818A] dark:text-slate-400 flex items-center gap-1 mb-2">
              <Sparkles className="h-3 w-3 text-[#087F8C]" /> Clinical Symptom Presets
            </span>
            <div className="flex flex-wrap gap-1.5">
              <button
                type="button"
                onClick={() =>
                  applySample(
                    "My 6-year-old child has had acute diarrhea, abdominal cramps and persistent vomiting for three days. High fever of 102F. We suspect tap water in Millbrook.",
                    "Millbrook"
                  )
                }
                className="rounded border border-[#E4EAE9] bg-white px-2 py-1 text-[11px] font-medium text-[#192D38] hover:border-[#087F8C] hover:text-[#087F8C] dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
              >
                Acute Gastroenteritis
              </button>
              <button
                type="button"
                onClick={() =>
                  applySample(
                    "Severe dry cough, chest tightness, burning throat and breathlessness worsening in evenings since chemical factory opened in Oldtown.",
                    "Oldtown"
                  )
                }
                className="rounded border border-[#E4EAE9] bg-white px-2 py-1 text-[11px] font-medium text-[#192D38] hover:border-[#087F8C] hover:text-[#087F8C] dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
              >
                Respiratory Irritation
              </button>
              <button
                type="button"
                onClick={() =>
                  applySample(
                    "Sudden high fever with severe joint pains and chills for two days following multiple mosquito bites around Riverside.",
                    "Riverside"
                  )
                }
                className="rounded border border-[#E4EAE9] bg-white px-2 py-1 text-[11px] font-medium text-[#192D38] hover:border-[#087F8C] hover:text-[#087F8C] dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200"
              >
                Vector-Borne Signs
              </button>
            </div>
          </div>

          <form onSubmit={submit} className="space-y-4">
            <div className="space-y-1">
              <div className="flex items-center justify-between">
                <Label htmlFor="symptom-text" className="text-xs font-semibold text-[#192D38] dark:text-slate-300 flex items-center gap-2">
                  Symptom History Narrative
                  {analyzing && <Loader2 className="h-3 w-3 animate-spin text-[#087F8C]" />}
                </Label>
                <span className="text-[11px] text-[#71818A]">{text.length} characters</span>
              </div>
              <Textarea
                id="symptom-text"
                required
                minLength={15}
                maxLength={8000}
                rows={6}
                value={text}
                onChange={(e) => onTextChange(e.target.value)}
                placeholder="Describe who is unwell (age/gender), primary symptoms (fever, vomiting, rash, cough), onset timeline, and potential exposures..."
                className="border-[#E4EAE9] text-xs focus-visible:ring-[#087F8C] dark:border-slate-700 dark:bg-slate-900"
              />
            </div>

            <div className="grid gap-3 sm:grid-cols-3">
              <div className="space-y-1">
                <Label htmlFor="district" className="text-xs font-semibold text-[#192D38] dark:text-slate-300">
                  Residential District
                </Label>
                <Input
                  id="district"
                  value={district}
                  onChange={(e) => setDistrict(e.target.value)}
                  placeholder="e.g. Millbrook"
                  className="h-9 border-[#E4EAE9] text-xs dark:border-slate-700 dark:bg-slate-900"
                />
              </div>

              <div className="space-y-1">
                <Label htmlFor="plat" className="text-[11px] font-medium text-[#71818A] dark:text-slate-400">
                  Latitude (opt)
                </Label>
                <Input
                  id="plat"
                  inputMode="decimal"
                  placeholder="17.6965"
                  value={lat}
                  onChange={(e) => setLat(e.target.value)}
                  className="h-9 text-xs border-[#E4EAE9] dark:border-slate-700 dark:bg-slate-900"
                />
              </div>

              <div className="space-y-1">
                <Label htmlFor="plng" className="text-[11px] font-medium text-[#71818A] dark:text-slate-400">
                  Longitude (opt)
                </Label>
                <Input
                  id="plng"
                  inputMode="decimal"
                  placeholder="83.2208"
                  value={lng}
                  onChange={(e) => setLng(e.target.value)}
                  className="h-9 text-xs border-[#E4EAE9] dark:border-slate-700 dark:bg-slate-900"
                />
              </div>
            </div>

            <Button
              type="submit"
              loading={submitting}
              className="w-full sm:w-auto h-9 bg-[#087F8C] hover:bg-[#066873] text-white font-medium text-xs px-5 shadow-sm"
            >
              <Send className="h-3.5 w-3.5 mr-1.5" /> Submit Health Report
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Live Clinical Entity Extraction Preview */}
      <Card className="lg:col-span-5 border-[#E4EAE9] bg-white shadow-subtle dark:border-slate-800 dark:bg-[#142B3B]">
        <CardHeader className="border-b border-[#E4EAE9] pb-4 dark:border-slate-800">
          <div className="flex items-center justify-between">
            <CardTitle className="text-sm font-bold text-[#192D38] dark:text-white flex items-center gap-2">
              <BrainCircuit className="h-4 w-4 text-[#087F8C]" /> Clinical NER & Triage Preview
            </CardTitle>
            <span className="rounded bg-[#DDF2F0] px-2 py-0.5 text-[10px] font-semibold text-[#087F8C] dark:bg-teal-950 dark:text-teal-300">
              Live Pipeline
            </span>
          </div>
          <CardDescription className="text-xs text-[#71818A] dark:text-slate-400">
            Real-time entity recognition for clinical review.
          </CardDescription>
        </CardHeader>
        <CardContent className="p-5">
          {!analysis ? (
            <div className="rounded-lg border border-dashed border-[#E4EAE9] p-8 text-center dark:border-slate-800">
              <Stethoscope className="h-8 w-8 mx-auto text-[#71818A] opacity-40 mb-2" />
              <p className="text-xs font-semibold text-[#192D38] dark:text-white">Awaiting Narrative</p>
              <p className="mt-1 text-[11px] text-[#71818A] dark:text-slate-400 max-w-xs mx-auto">
                Type symptoms in natural language to view medical entity tagging and urgency categorization.
              </p>
            </div>
          ) : (
            <div className="space-y-4 text-xs">
              <div className="rounded-lg border border-[#E4EAE9] bg-[#F7F8F6] p-3 dark:border-slate-800 dark:bg-slate-900/60">
                <div className="flex items-center justify-between mb-2">
                  <span className="font-semibold text-[#192D38] dark:text-white">Triage Severity</span>
                  <UrgencyBadge urgency={analysis.urgency} />
                </div>
                <div className="flex items-center justify-between text-[11px] text-[#71818A] dark:text-slate-400 mb-1">
                  <span>Urgency Score</span>
                  <span className="font-mono font-semibold text-[#087F8C]">
                    {analysis.urgency_score?.toFixed(2) ?? "—"}
                  </span>
                </div>
                <ProgressBar value={analysis.urgency_score ?? 0} className="h-1.5 bg-[#E4EAE9]" />
              </div>

              {/* Symptoms chips */}
              <div className="rounded-md border border-[#E4EAE9] p-3 dark:border-slate-800">
                <p className="font-semibold text-[#192D38] dark:text-white mb-2 flex items-center gap-1">
                  <Pill className="h-3.5 w-3.5 text-[#087F8C]" /> Recognized Clinical Symptoms
                </p>
                <div className="flex flex-wrap gap-1.5">
                  {(analysis.symptoms ?? []).map((s) => (
                    <span
                      key={s}
                      className="rounded bg-[#DDF2F0] px-2 py-0.5 text-[11px] font-semibold text-[#087F8C] border border-[#B2E4E0] dark:bg-teal-950 dark:text-teal-300 dark:border-teal-800"
                    >
                      {titleCase(s)}
                    </span>
                  ))}
                  {!(analysis.symptoms ?? []).length && (
                    <span className="text-[11px] text-[#71818A]">No clinical keywords identified yet</span>
                  )}
                </div>
              </div>

              {/* Structured digest */}
              {analysis.digest && (
                <div className="rounded-md border border-[#E4EAE9] bg-[#F7F8F6] p-3 dark:border-slate-800 dark:bg-slate-900/60">
                  <p className="font-semibold text-[#192D38] dark:text-white mb-1">Extractive Structured Digest</p>
                  <p className="text-[11px] text-[#71818A] dark:text-slate-300 leading-relaxed">
                    {analysis.digest}
                  </p>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

/* -------------------------------- My reports -------------------------------- */
function MyReports() {
  const [data, setData] = React.useState<MedicalReport[] | null>(null);
  const [selectedReport, setSelectedReport] = React.useState<MedicalReport | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(true);

  const load = React.useCallback(async () => {
    setLoading(true);
    try {
      const page = await api.get<{ items: MedicalReport[] }>("/reports?page_size=50");
      setData(page.items);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load health reports");
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    load();
  }, [load]);

  if (error) return <ErrorState message={error} retry={load} />;
  if (loading) return <LoadingState label="Retrieving your medical symptom history…" />;
  if (!data || data.length === 0) {
    return (
      <EmptyState
        title="No health reports logged yet"
        description="Share your symptoms or upload a clinical record to track observations."
      />
    );
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {data.map((r) => (
          <Card
            key={r.id}
            onClick={() => setSelectedReport(r)}
            className="border-[#E4EAE9] bg-white shadow-subtle hover:border-[#087F8C]/60 hover:shadow-card transition-all cursor-pointer dark:border-slate-800 dark:bg-[#142B3B]"
          >
            <CardContent className="p-4 sm:p-5 flex flex-col justify-between h-full">
              <div>
                <div className="flex items-center justify-between border-b border-[#E4EAE9]/60 pb-2.5 dark:border-slate-800">
                  <span className="flex items-center gap-1.5 text-xs font-bold text-[#087F8C]">
                    <Stethoscope className="h-3.5 w-3.5" /> Report #{r.id}
                  </span>
                  <UrgencyBadge urgency={r.urgency} />
                </div>

                <p className="mt-2.5 text-xs text-[#71818A] dark:text-slate-300 line-clamp-3 leading-relaxed">
                  {r.text}
                </p>

                <div className="mt-3 flex flex-wrap gap-1">
                  {(r.symptoms ?? []).slice(0, 4).map((s) => (
                    <span
                      key={s}
                      className="rounded bg-[#F7F8F6] px-1.5 py-0.5 text-[10px] font-semibold text-[#192D38] border border-[#E4EAE9] dark:bg-slate-800 dark:border-slate-700 dark:text-slate-300"
                    >
                      {titleCase(s)}
                    </span>
                  ))}
                  {(r.symptoms ?? []).length > 4 && (
                    <span className="rounded bg-slate-100 px-1.5 py-0.5 text-[10px] text-[#71818A]">
                      +{(r.symptoms?.length ?? 0) - 4} more
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

      {/* Detail Dialog */}
      {selectedReport && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-[#142B3B]/60 backdrop-blur-xs p-4"
          onClick={() => setSelectedReport(null)}
        >
          <Card
            className="w-full max-w-xl max-h-[85vh] overflow-y-auto border-[#E4EAE9] bg-white shadow-elevated dark:border-slate-800 dark:bg-[#142B3B]"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-[#E4EAE9] p-5 dark:border-slate-800">
              <div className="flex items-center gap-2">
                <Stethoscope className="h-4 w-4 text-[#087F8C]" />
                <h2 className="text-base font-bold text-[#192D38] dark:text-white">Health Report #{selectedReport.id}</h2>
              </div>
              <button
                onClick={() => setSelectedReport(null)}
                className="rounded p-1 text-[#71818A] hover:bg-[#F7F8F6] dark:hover:bg-slate-800"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <CardContent className="p-6 space-y-4 text-xs">
              <div className="flex items-center justify-between">
                <span className="text-xs text-[#71818A]">Triage Assessment:</span>
                <UrgencyBadge urgency={selectedReport.urgency} />
              </div>

              <div className="rounded-md border border-[#E4EAE9] bg-[#F7F8F6] p-3 dark:border-slate-800 dark:bg-slate-900/60">
                <p className="font-semibold text-[#192D38] dark:text-white mb-1">Patient Narrative</p>
                <p className="text-[#71818A] dark:text-slate-300 leading-relaxed whitespace-pre-line">
                  {selectedReport.text}
                </p>
              </div>

              {selectedReport.summary && (
                <div className="rounded-md border border-[#087F8C]/30 bg-[#DDF2F0]/30 p-3 text-[#142B3B] dark:border-teal-800 dark:bg-teal-950/30 dark:text-teal-200">
                  <p className="font-bold flex items-center gap-1.5 text-xs mb-1">
                    <Sparkles className="h-3.5 w-3.5 text-[#087F8C]" /> Extractive Clinical Summary
                  </p>
                  <p className="text-xs leading-relaxed">{selectedReport.summary}</p>
                </div>
              )}

              <div>
                <p className="font-semibold text-[#192D38] dark:text-white mb-1.5">Identified Medical Symptoms</p>
                <div className="flex flex-wrap gap-1.5">
                  {(selectedReport.symptoms ?? []).map((s) => (
                    <span
                      key={s}
                      className="rounded bg-[#DDF2F0] px-2 py-0.5 text-xs font-semibold text-[#087F8C] border border-[#B2E4E0] dark:bg-teal-950 dark:text-teal-300"
                    >
                      {titleCase(s)}
                    </span>
                  ))}
                </div>
              </div>

              <div className="border-t border-[#E4EAE9] pt-3 flex justify-between text-[#71818A] dark:border-slate-800">
                <span>Submitted: {formatDateTime(selectedReport.created_at)}</span>
                {selectedReport.district && <span>District: {selectedReport.district}</span>}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}

/* ------------------------------- My documents ------------------------------- */
function MyDocuments({ onReportGenerated }: { onReportGenerated: () => void }) {
  const { toast } = useToast();
  const fileRef = React.useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = React.useState(false);
  const [generatingId, setGeneratingId] = React.useState<number | null>(null);
  const [docs, setDocs] = React.useState<DocumentMeta[] | null>(null);
  const [error, setError] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(true);

  const load = React.useCallback(async () => {
    setLoading(true);
    try {
      const page = await api.get<{ items: DocumentMeta[] }>("/documents?page_size=50");
      setDocs(page.items);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load clinical documents");
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    load();
  }, [load]);

  async function onUpload(file: File) {
    setUploading(true);
    try {
      const form = new FormData();
      form.append("file", file);
      const doc = await api.upload<DocumentMeta>("/documents/upload", form);
      toast("Document processed", {
        variant: "success",
        description:
          doc.extraction_status === "EXTRACTED"
            ? "Clinical text extracted locally"
            : `Extraction status: ${doc.extraction_status}`,
      });
      load();
    } catch (err) {
      toast("Upload failed", {
        variant: "error",
        description: err instanceof Error ? err.message : undefined,
      });
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  }

  async function createReport(doc: DocumentMeta) {
    setGeneratingId(doc.id);
    try {
      await api.post<MedicalReport>("/reports/from-document", { document_id: doc.id });
      toast("Health report created from document", { variant: "success" });
      onReportGenerated();
    } catch (err) {
      toast("Could not generate report", {
        variant: "error",
        description: err instanceof Error ? err.message : undefined,
      });
    } finally {
      setGeneratingId(null);
    }
  }

  async function remove(doc: DocumentMeta) {
    try {
      await api.delete(`/documents/${doc.id}`);
      toast("Document removed", { variant: "success" });
      load();
    } catch (err) {
      toast("Delete failed", {
        variant: "error",
        description: err instanceof Error ? err.message : undefined,
      });
    }
  }

  return (
    <div className="space-y-6">
      {/* Upload Zone */}
      <Card className="border-[#E4EAE9] bg-white shadow-subtle dark:border-slate-800 dark:bg-[#142B3B]">
        <CardContent className="p-6">
          <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-[#E4EAE9] p-8 text-center bg-[#F7F8F6]/50 dark:border-slate-800 dark:bg-slate-900/40">
            <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[#DDF2F0] text-[#087F8C] dark:bg-teal-950 dark:text-teal-300">
              <Upload className="h-6 w-6" />
            </div>
            <div>
              <p className="text-sm font-bold text-[#192D38] dark:text-white">Upload Medical Documentation</p>
              <p className="mt-1 text-xs text-[#71818A] dark:text-slate-400 max-w-md">
                Upload clinical notes, lab summaries, or hospital discharge summaries in PDF or TXT format (up to 20MB). Extracted with zero cloud leakage.
              </p>
            </div>
            <input
              ref={fileRef}
              type="file"
              accept=".pdf,.txt,.md"
              className="hidden"
              id="doc-upload"
              onChange={(e) => e.target.files?.[0] && onUpload(e.target.files[0])}
            />
            <Button
              loading={uploading}
              onClick={() => fileRef.current?.click()}
              className="mt-2 h-9 bg-[#087F8C] hover:bg-[#066873] text-white text-xs font-semibold px-4"
            >
              <FileUp className="h-3.5 w-3.5 mr-1.5" /> Select Medical File
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Document Library */}
      {error ? (
        <ErrorState message={error} retry={load} />
      ) : loading ? (
        <LoadingState label="Loading medical vault…" />
      ) : !docs || docs.length === 0 ? (
        <EmptyState
          title="No documents uploaded"
          description="Your uploaded prescription notes and PDF summaries will be listed here with clinical text extraction."
        />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2">
          {docs.map((d) => (
            <Card
              key={d.id}
              className="border-[#E4EAE9] bg-white shadow-subtle dark:border-slate-800 dark:bg-[#142B3B]"
            >
              <CardContent className="p-5">
                <div className="flex items-start justify-between gap-2 border-b border-[#E4EAE9]/60 pb-3 dark:border-slate-800">
                  <div className="min-w-0">
                    <p className="truncate text-xs font-bold text-[#192D38] dark:text-white flex items-center gap-1.5">
                      <FileText className="h-4 w-4 text-[#087F8C]" />
                      {d.filename}
                    </p>
                    <p className="mt-1 text-[11px] text-[#71818A] dark:text-slate-400">
                      {(d.size_bytes / 1024).toFixed(1)} KB · {formatDateTime(d.created_at)}
                      {d.pages ? ` · ${d.pages} pages` : ""}
                    </p>
                  </div>
                  <span
                    className={`rounded px-2 py-0.5 text-[10px] font-semibold border ${
                      d.extraction_status === "EXTRACTED"
                        ? "bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950 dark:text-emerald-300 dark:border-emerald-800"
                        : "bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300"
                    }`}
                  >
                    {titleCase(d.extraction_status)}
                  </span>
                </div>

                <div className="mt-4 flex items-center justify-between">
                  <Button
                    size="sm"
                    onClick={() => createReport(d)}
                    loading={generatingId === d.id}
                    className="h-8 bg-[#087F8C] hover:bg-[#066873] text-white text-xs font-medium px-3"
                  >
                    <Sparkles className="h-3 w-3 mr-1.5" /> Convert to Report
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => remove(d)}
                    className="h-8 text-xs text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40"
                  >
                    <Trash2 className="h-3.5 w-3.5 mr-1" /> Delete
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
