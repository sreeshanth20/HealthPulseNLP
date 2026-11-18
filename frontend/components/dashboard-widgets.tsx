"use client";

import * as React from "react";
import { AlertTriangle, Inbox, ServerCrash, ShieldAlert } from "lucide-react";
import { Badge, Button, Card, Skeleton, Spinner } from "@/components/ui/core";
import { cn, titleCase } from "@/lib/utils";
import type { AlertEvidence } from "@/lib/types";

/* ------------------------------- Status badges ------------------------------ */
export function UrgencyBadge({ urgency }: { urgency: string }) {
  const map: Record<string, { className: string; label: string; dot: string }> = {
    LOW: {
      className: "bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950/40 dark:text-emerald-300 dark:border-emerald-800",
      dot: "bg-emerald-600 dark:bg-emerald-400",
      label: "Low Urgency",
    },
    MEDIUM: {
      className: "bg-[#DDF2F0] text-[#087F8C] border-[#B2E4E0] dark:bg-teal-950/40 dark:text-teal-300 dark:border-teal-800",
      dot: "bg-[#087F8C] dark:bg-teal-400",
      label: "Medium Urgency",
    },
    HIGH: {
      className: "bg-amber-50 text-amber-900 border-amber-200 dark:bg-amber-950/40 dark:text-amber-300 dark:border-amber-800",
      dot: "bg-amber-600 dark:bg-amber-400",
      label: "High Urgency",
    },
    CRITICAL: {
      className: "bg-rose-50 text-rose-900 border-rose-200 dark:bg-rose-950/40 dark:text-rose-300 dark:border-rose-800",
      dot: "bg-rose-600 dark:bg-rose-400",
      label: "Critical Urgency",
    },
  };
  const conf = map[urgency] ?? {
    className: "bg-secondary text-secondary-foreground border-border",
    dot: "bg-muted-foreground",
    label: titleCase(urgency),
  };
  return (
    <span className={cn("inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-medium tracking-tight", conf.className)}>
      <span className={cn("h-1.5 w-1.5 rounded-full", conf.dot)} />
      {conf.label}
    </span>
  );
}

export function StatusBadge({ status }: { status: string }) {
  const map: Record<string, { className: string; label: string }> = {
    SUBMITTED: {
      className: "bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-950/30 dark:text-amber-300 dark:border-amber-800",
      label: "Submitted",
    },
    ACKNOWLEDGED: {
      className: "bg-[#DDF2F0] text-[#087F8C] border-[#B2E4E0] dark:bg-teal-950/30 dark:text-teal-300 dark:border-teal-800",
      label: "Acknowledged",
    },
    IN_PROGRESS: {
      className: "bg-blue-50 text-blue-800 border-blue-200 dark:bg-blue-950/30 dark:text-blue-300 dark:border-blue-800",
      label: "In Progress",
    },
    RESOLVED: {
      className: "bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-300 dark:border-emerald-800",
      label: "Resolved",
    },
    REJECTED: {
      className: "bg-rose-50 text-rose-800 border-rose-200 dark:bg-rose-950/30 dark:text-rose-300 dark:border-rose-800",
      label: "Rejected",
    },
    NEW: {
      className: "bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-950/30 dark:text-amber-300 dark:border-amber-800",
      label: "New",
    },
    REVIEWING: {
      className: "bg-[#DDF2F0] text-[#087F8C] border-[#B2E4E0] dark:bg-teal-950/30 dark:text-teal-300 dark:border-teal-800",
      label: "Under Review",
    },
    CONFIRMED: {
      className: "bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-300 dark:border-emerald-800",
      label: "Confirmed Alert",
    },
    DISMISSED: {
      className: "bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-900 dark:text-slate-400 dark:border-slate-800",
      label: "Dismissed",
    },
    OPEN: {
      className: "bg-amber-50 text-amber-800 border-amber-200 dark:bg-amber-950/30 dark:text-amber-300 dark:border-amber-800",
      label: "Open Case",
    },
    FIELD_VISIT_SCHEDULED: {
      className: "bg-indigo-50 text-indigo-800 border-indigo-200 dark:bg-indigo-950/30 dark:text-indigo-300 dark:border-indigo-800",
      label: "Field Visit",
    },
    SAMPLING: {
      className: "bg-purple-50 text-purple-800 border-purple-200 dark:bg-purple-950/30 dark:text-purple-300 dark:border-purple-800",
      label: "Lab Sampling",
    },
    CLOSED_RESOLVED: {
      className: "bg-emerald-50 text-emerald-800 border-emerald-200 dark:bg-emerald-950/30 dark:text-emerald-300 dark:border-emerald-800",
      label: "Closed (Resolved)",
    },
    CLOSED_NO_ACTION: {
      className: "bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-900 dark:text-slate-400 dark:border-slate-800",
      label: "Closed (No Action)",
    },
  };
  const conf = map[status] ?? {
    className: "bg-secondary text-secondary-foreground border-border",
    label: titleCase(status),
  };
  return (
    <span className={cn("inline-flex items-center rounded-md border px-2 py-0.5 text-xs font-medium", conf.className)}>
      {conf.label}
    </span>
  );
}

export function CategoryBadge({ category }: { category: string }) {
  return (
    <span className="inline-flex items-center rounded border border-[#E4EAE9] bg-[#F7F8F6] px-2 py-0.5 text-xs font-medium text-[#192D38] dark:border-slate-700 dark:bg-slate-800/80 dark:text-slate-200">
      {titleCase(category)}
    </span>
  );
}

/* --------------------------------- Stat card -------------------------------- */
export function StatCard({
  label,
  value,
  hint,
  icon,
  className,
}: {
  label: string;
  value: React.ReactNode;
  hint?: string;
  icon?: React.ReactNode;
  className?: string;
}) {
  return (
    <Card className={cn("relative overflow-hidden border border-[#E4EAE9] bg-white p-5 shadow-subtle dark:border-slate-800 dark:bg-[#142B3B]", className)}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="text-[11px] font-semibold uppercase tracking-wider text-[#71818A] dark:text-slate-400">{label}</p>
          <p className="mt-2 text-2xl font-bold tracking-tight text-[#192D38] dark:text-white">{value}</p>
          {hint && <p className="mt-1 text-xs text-[#71818A] dark:text-slate-400">{hint}</p>}
        </div>
        {icon && (
          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#DDF2F0] text-[#087F8C] dark:bg-teal-950/60 dark:text-teal-400">
            {icon}
          </div>
        )}
      </div>
    </Card>
  );
}

/* ------------------------------- Page states -------------------------------- */
export function LoadingState({ label = "Loading data…" }: { label?: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-[#E4EAE9] bg-white p-12 text-center shadow-subtle dark:border-slate-800 dark:bg-[#142B3B]">
      <Spinner className="h-6 w-6 text-[#087F8C]" />
      <p className="text-sm font-medium text-[#71818A] dark:text-slate-300">{label}</p>
      <div className="mt-2 grid w-full max-w-sm gap-2">
        <Skeleton className="h-3 w-3/4 mx-auto" />
        <Skeleton className="h-3 w-1/2 mx-auto" />
      </div>
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
}: {
  title: string;
  description?: string;
  action?: React.ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-dashed border-[#E4EAE9] bg-white p-12 text-center dark:border-slate-800 dark:bg-[#142B3B]/60">
      <div className="flex h-12 w-12 items-center justify-center rounded-full bg-[#F7F8F6] text-[#71818A] dark:bg-slate-800 dark:text-slate-400">
        <Inbox className="h-6 w-6" />
      </div>
      <div>
        <p className="text-sm font-semibold text-[#192D38] dark:text-white">{title}</p>
        {description && <p className="mt-1 max-w-sm text-xs text-[#71818A] dark:text-slate-400">{description}</p>}
      </div>
      {action && <div className="mt-2">{action}</div>}
    </div>
  );
}

export function ErrorState({ message, retry }: { message: string; retry?: () => void }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 rounded-lg border border-rose-200 bg-rose-50/60 p-10 text-center dark:border-rose-900/60 dark:bg-rose-950/20">
      <div className="flex h-10 w-10 items-center justify-center rounded-full bg-rose-100 text-rose-600 dark:bg-rose-900/40 dark:text-rose-400">
        <ServerCrash className="h-5 w-5" />
      </div>
      <p className="text-sm font-semibold text-rose-900 dark:text-rose-200">Unable to load data</p>
      <p className="max-w-md text-xs text-rose-700 dark:text-rose-300">{message}</p>
      {retry && (
        <Button variant="outline" size="sm" onClick={retry} className="mt-1 border-rose-200 bg-white text-rose-800 hover:bg-rose-50 dark:border-rose-800 dark:bg-slate-900 dark:text-rose-200">
          Try again
        </Button>
      )}
    </div>
  );
}

export function DisclaimerNote({ children }: { children?: React.ReactNode }) {
  return (
    <div className="flex items-start gap-3 rounded-lg border border-[#E4EAE9] bg-[#F7F8F6] p-4 text-xs leading-relaxed text-[#192D38] dark:border-slate-800 dark:bg-slate-900/80 dark:text-slate-300">
      <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0 text-[#087F8C]" />
      <div>
        <p className="font-semibold text-[#142B3B] dark:text-teal-300">Clinical & Epidemiological Advisory</p>
        <p className="mt-0.5 text-[#71818A] dark:text-slate-400">
          {children ||
            "Association signals are statistical co-occurrence indicators. They are not medical diagnoses, not clinical risk probabilities, and never prove causal origin. All correlation alerts require ground verification by qualified public health and municipal officers."}
        </p>
      </div>
    </div>
  );
}

/* ------------------------------ Evidence panel ------------------------------ */
function EvidenceRow({ evidence }: { evidence: AlertEvidence }) {
  const parts: string[] = [];
  if (typeof evidence.association_score === "number") {
    parts.push(`Association: ${evidence.association_score.toFixed(2)}`);
  }
  if (typeof evidence.semantic_similarity === "number") {
    parts.push(`Semantic: ${(evidence.semantic_similarity * 100).toFixed(0)}%`);
  }
  if (typeof evidence.spatial_proximity === "number") {
    parts.push(
      evidence.distance_km != null ? `Proximity: ${evidence.distance_km} km` : "Location overlap"
    );
  }
  if (typeof evidence.gap_days === "number") {
    parts.push(`Temporal Lag: ${evidence.gap_days}d`);
  }
  if (typeof evidence.theme_match === "number") {
    parts.push(`Theme Match: ${(evidence.theme_match * 100).toFixed(0)}%`);
  }
  if (typeof evidence.lift === "number") {
    parts.push(`Lift: ×${evidence.lift.toFixed(1)}`);
  }

  return (
    <div className="rounded-md border border-[#E4EAE9] bg-[#F7F8F6] p-3 text-xs dark:border-slate-800 dark:bg-slate-900/60">
      <div className="flex flex-wrap gap-1.5">
        {parts.map((p) => (
          <span key={p} className="rounded bg-white px-2 py-0.5 font-mono text-[11px] font-medium text-[#203A4A] border border-[#E4EAE9] dark:border-slate-700 dark:bg-slate-800 dark:text-slate-200">
            {p}
          </span>
        ))}
      </div>
      {typeof evidence.complaint_excerpt === "string" && evidence.complaint_excerpt && (
        <p className="mt-2 text-xs italic text-[#71818A] dark:text-slate-400 border-l-2 border-[#087F8C] pl-2">
          “{evidence.complaint_excerpt}”
        </p>
      )}
      {Array.isArray(evidence.report_symptoms) && evidence.report_symptoms.length > 0 && (
        <p className="mt-1.5 text-xs text-[#192D38] dark:text-slate-300">
          <span className="font-semibold text-[#71818A] dark:text-slate-400">Co-occurring Symptoms:</span>{" "}
          {evidence.report_symptoms.join(", ")}
        </p>
      )}
    </div>
  );
}

export function EvidencePanel({ evidence }: { evidence: AlertEvidence[] | null }) {
  if (!evidence || evidence.length === 0) {
    return <p className="text-xs text-[#71818A]">No structured statistical evidence items attached.</p>;
  }
  return (
    <div className="space-y-2">
      <p className="flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wider text-[#71818A] dark:text-slate-400">
        <ShieldAlert className="h-3.5 w-3.5 text-[#087F8C]" /> Correlated Evidence ({evidence.length})
      </p>
      {evidence.slice(0, 8).map((ev, i) => (
        <EvidenceRow key={i} evidence={ev} />
      ))}
    </div>
  );
}

/* ------------------------------ Pagination bar ------------------------------ */
export function PaginationBar({
  page,
  pages,
  onPage,
}: {
  page: number;
  pages: number;
  onPage: (page: number) => void;
}) {
  if (pages <= 1) return null;
  return (
    <div className="flex items-center justify-between border-t border-[#E4EAE9] pt-3 text-xs dark:border-slate-800">
      <Button
        variant="outline"
        size="sm"
        disabled={page <= 1}
        onClick={() => onPage(page - 1)}
        className="h-8 border-[#E4EAE9] text-xs hover:bg-[#F7F8F6] dark:border-slate-800"
      >
        Previous
      </Button>
      <span className="text-xs font-medium text-[#71818A] dark:text-slate-400">
        Page <span className="font-semibold text-[#192D38] dark:text-white">{page}</span> of {pages}
      </span>
      <Button
        variant="outline"
        size="sm"
        disabled={page >= pages}
        onClick={() => onPage(page + 1)}
        className="h-8 border-[#E4EAE9] text-xs hover:bg-[#F7F8F6] dark:border-slate-800"
      >
        Next
      </Button>
    </div>
  );
}
