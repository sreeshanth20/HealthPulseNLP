// Shared TypeScript types mirroring the FastAPI schemas.

export type Role =
  | "CITIZEN"
  | "PATIENT"
  | "CLINICIAN"
  | "MUNICIPAL_ADMIN"
  | "HEALTH_ADMIN"
  | "SUPER_ADMIN";

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: Role;
  is_active: boolean;
  phone?: string | null;
  created_at: string;
  last_login_at?: string | null;
}

export interface Urgency {
  label: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  score: number;
  reasons: string[];
}

export interface LocationInfo {
  raw_text?: string | null;
  district?: string | null;
  lat?: number | null;
  lng?: number | null;
  pincode?: string | null;
  confidence: number;
  source?: string | null;
}

export interface ComplaintAnalysis {
  category: string;
  category_confidence: number;
  category_scores: Record<string, number>;
  classifier_method: string;
  matched_terms: string[];
  urgency: Urgency;
  location: LocationInfo;
  language?: string | null;
}

export interface DuplicateCandidate {
  id: number;
  title?: string | null;
  text: string;
  category?: string | null;
  district?: string | null;
  score: number;
  is_duplicate: boolean;
  signals: Record<string, unknown>;
}

export interface Complaint {
  id: number;
  title: string;
  text: string;
  category: string;
  category_confidence: number;
  urgency: string;
  urgency_score: number;
  urgency_reasons?: string[] | null;
  language?: string | null;
  district?: string | null;
  address?: string | null;
  lat?: number | null;
  lng?: number | null;
  status: string;
  duplicate_of_id?: number | null;
  duplicate_score?: number | null;
  resolution_note?: string | null;
  created_at: string;
  resolved_at?: string | null;
  reporter_id?: number | null;
}

export interface Entity {
  text: string;
  canonical: string;
  type: string;
  start: number;
  end: number;
  confidence: number;
}

export interface MedicalReport {
  id: number;
  text: string;
  language?: string | null;
  entities?: Entity[] | null;
  symptoms?: string[] | null;
  symptom_categories?: string[] | null;
  ner_backend?: string | null;
  entity_count?: number;
  urgency: string;
  urgency_score: number;
  urgency_reasons?: string[] | null;
  summary?: string | null;
  digest?: string | null;
  district?: string | null;
  lat?: number | null;
  lng?: number | null;
  status: string;
  created_at: string;
  patient_id?: number | null;
  patient_alias?: string | null;
  document_id?: number | null;
}

export interface DocumentMeta {
  id: number;
  filename: string;
  mime?: string | null;
  size_bytes: number;
  sha256: string;
  pages?: number | null;
  extraction_status: string;
  report_id?: number | null;
  created_at: string;
  uploader_id?: number | null;
}

export interface AlertEvidence {
  kind?: string;
  association_score?: number;
  semantic_similarity?: number;
  spatial_proximity?: number;
  distance_km?: number | null;
  temporal_proximity?: number;
  gap_days?: number;
  theme_match?: number;
  complaint_excerpt?: string;
  report_symptoms?: string[];
  observed?: number;
  expected?: number;
  lift?: number;
  methods?: string[];
  [key: string]: unknown;
}

export interface Alert {
  id: number;
  type: string;
  title: string;
  interpretation?: string | null;
  disclaimer?: string | null;
  score: number;
  districts?: string[] | null;
  complaint_categories?: string[] | null;
  n_complaints: number;
  n_reports: number;
  n_supporting_pairs: number;
  evidence?: AlertEvidence[] | null;
  status: string;
  status_note?: string | null;
  created_at: string;
}

export interface Investigation {
  id: number;
  alert_id: number;
  title?: string | null;
  status: string;
  notes?: string | null;
  findings?: string | null;
  created_at: string;
  updated_at: string;
  closed_at?: string | null;
  assigned_to_id?: number | null;
}

export interface Page<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface DashboardStats {
  total_complaints?: number;
  open_complaints?: number;
  resolved_complaints?: number;
  complaints_last_14d?: number;
  status_breakdown?: Record<string, number>;
  category_breakdown?: Record<string, number>;
  urgency_breakdown?: Record<string, number>;
  total_reports?: number;
  reports_last_14d?: number;
  urgency_reports?: Record<string, number>;
  open_alerts?: number;
  open_investigations?: number;
  top_symptoms?: { symptom: string; count: number }[];
  trend?: { days: number; points: { date: string; complaints: number; reports: number }[] };
  total_users?: number;
  active_users?: number;
  users_by_role?: Record<string, number>;
  my_complaints?: number;
  my_open_complaints?: number;
  my_reports?: number;
  recent_complaints?: { id: number; title: string; status: string; category: string; created_at: string }[];
}

export interface AuditEntry {
  id: number;
  actor_id?: number | null;
  actor_role?: string | null;
  action: string;
  entity_type: string;
  entity_id?: string | null;
  detail?: string | null;
  ip?: string | null;
  created_at: string;
}

export const ROLE_LABELS: Record<Role, string> = {
  CITIZEN: "Citizen",
  PATIENT: "Patient",
  CLINICIAN: "Healthcare Professional",
  MUNICIPAL_ADMIN: "Municipal Administrator",
  HEALTH_ADMIN: "Public Health Administrator",
  SUPER_ADMIN: "Super Administrator",
};

export const ROLE_HOME: Record<Role, string> = {
  CITIZEN: "/dashboard/citizen",
  PATIENT: "/dashboard/patient",
  CLINICIAN: "/dashboard/clinician",
  MUNICIPAL_ADMIN: "/dashboard/municipal",
  HEALTH_ADMIN: "/dashboard/health",
  SUPER_ADMIN: "/dashboard/superadmin",
};
