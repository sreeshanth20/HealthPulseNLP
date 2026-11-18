import Link from "next/link";
import {
  Activity,
  ArrowRight,
  BarChart3,
  BrainCircuit,
  CheckCircle2,
  FileCheck2,
  FileText,
  FlaskConical,
  HeartPulse,
  Lock,
  MapPin,
  Megaphone,
  ShieldAlert,
  ShieldCheck,
  Sparkles,
  Stethoscope,
  Users,
} from "lucide-react";
import { Badge, Button, Card, CardContent } from "@/components/ui/core";
import { ThemeToggle } from "@/components/theme";
import { StatCard } from "@/components/dashboard-widgets";

const ENGINES = [
  {
    icon: Megaphone,
    title: "Civic Environmental Triage",
    badge: "NLP Classification",
    points: [
      "On-device classification across 10 environmental categories",
      "Automated location entity parsing with geographic geocoding",
      "Near-duplicate detection on recurrent citizen grievance submissions",
      "Explainable urgency prioritization and severity triage scoring",
    ],
  },
  {
    icon: Stethoscope,
    title: "Clinical Symptom Surveillance",
    badge: "Medical NER",
    points: [
      "Natural language symptom intake with zero cloud data leakage",
      "Medical prescription and clinical lab summary PDF text extraction",
      "Clinical entity recognition (symptoms, medications, durations)",
      "Automated extractive clinical digests (strictly non-diagnostic)",
    ],
  },
  {
    icon: BrainCircuit,
    title: "Cross-Domain Anomaly Engine",
    badge: "Spatio-Temporal Scan",
    points: [
      "Semantic embedding similarity linking environmental hazards to symptoms",
      "Configurable spatial proximity and temporal lag correlation windows",
      "Statistical lift and co-occurrence scoring flagging potential outbreaks",
      "Evidence-backed alert generation with auditable candidate pair tracking",
    ],
  },
  {
    icon: BarChart3,
    title: "Administrative Operations",
    badge: "Enterprise RBAC",
    points: [
      "Six dedicated role-based dashboards with strict data segregation",
      "Interactive GIS ward cluster heatmaps and multi-ward trend monitoring",
      "Municipal grievance lifecycle management and status transition audit",
      "Cryptographically sequenced security audit logs with CSV export",
    ],
  },
];

const ROLES = [
  {
    icon: Megaphone,
    title: "Citizen",
    tag: "Civic Reporting",
    text: "Submit localized reports on water discoloration, open sewage, garbage dumps, and pesticide odors with instant NLP triage and duplicate prevention.",
  },
  {
    icon: HeartPulse,
    title: "Patient",
    tag: "Clinical Vault",
    text: "Log voluntary symptom histories, maintain a private clinical document vault, and convert uploaded medical records into structured symptom digests.",
  },
  {
    icon: Stethoscope,
    title: "Healthcare Professional",
    tag: "Clinical Review",
    text: "Review de-identified symptom feeds, inspect recognized medical entities, evaluate clinical triage priority, and regenerate structured case summaries.",
  },
  {
    icon: Users,
    title: "Municipal Administrator",
    tag: "Civic Operations",
    text: "Coordinate public works, dispatch remediation teams on live GIS maps, group duplicate complaints into master records, and log remediation outcomes.",
  },
  {
    icon: FlaskConical,
    title: "Public Health Administrator",
    tag: "Epidemiological Intelligence",
    text: "Execute automated cross-domain correlation scans, review evidence-backed statistical co-occurrence alerts, and direct field investigations.",
  },
  {
    icon: ShieldCheck,
    title: "Super Administrator",
    tag: "Platform Governance",
    text: "Manage role provisioning, oversee ML inference pipeline telemetry, monitor database counts, and inspect immutable security audit trails.",
  },
];

async function fetchPublicStats() {
  const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";
  try {
    const res = await fetch(`${API_URL}/analytics/public`, { next: { revalidate: 30 } });
    if (!res.ok) return null;
    return (await res.json()) as {
      total_complaints: number;
      resolved_complaints: number;
      resolution_rate: number;
      districts_covered: number;
      categories: Record<string, number>;
    };
  } catch {
    return null;
  }
}

export default async function LandingPage() {
  const stats = await fetchPublicStats();

  return (
    <div className="min-h-screen bg-[#F7F8F6] text-[#192D38] dark:bg-[#102330] dark:text-[#F7F8F6]">
      {/* Enterprise Top Navigation */}
      <header className="sticky top-0 z-40 border-b border-[#E4EAE9] bg-white/95 backdrop-blur dark:border-slate-800 dark:bg-[#142B3B]/95">
        <div className="container flex h-16 items-center justify-between">
          <Link href="/" className="flex items-center gap-2.5 font-bold tracking-tight text-[#142B3B] dark:text-white">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#087F8C] text-white shadow-sm">
              <Activity className="h-5 w-5" />
            </span>
            <div className="flex flex-col">
              <span className="text-base font-extrabold leading-tight">
                HealthPulse <span className="text-[#087F8C]">AI</span>
              </span>
              <span className="text-[10px] font-medium text-[#71818A] dark:text-slate-400">
                Healthcare & Civic Intelligence
              </span>
            </div>
          </Link>

          <nav className="hidden items-center gap-7 text-xs font-semibold text-[#71818A] md:flex dark:text-slate-300">
            <a href="#platform" className="hover:text-[#087F8C] transition-colors">Intelligence Engines</a>
            <a href="#how" className="hover:text-[#087F8C] transition-colors">Pipeline Architecture</a>
            <a href="#roles" className="hover:text-[#087F8C] transition-colors">User Roles</a>
            <a href="#ethics" className="hover:text-[#087F8C] transition-colors">Responsible AI</a>
          </nav>

          <div className="flex items-center gap-2.5">
            <ThemeToggle />
            <Link href="/login">
              <Button variant="outline" size="sm" className="h-8.5 border-[#E4EAE9] text-xs font-semibold hover:bg-[#F7F8F6] dark:border-slate-700">
                Sign In
              </Button>
            </Link>
            <Link href="/register">
              <Button size="sm" className="h-8.5 bg-[#087F8C] hover:bg-[#066873] text-white text-xs font-semibold shadow-sm">
                Get Started
              </Button>
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section className="relative overflow-hidden border-b border-[#E4EAE9] bg-white py-20 lg:py-28 dark:border-slate-800 dark:bg-[#142B3B]">
        <div className="pointer-events-none absolute inset-0 bg-[radial-gradient(#087F8C_1px,transparent_1px)] [background-size:24px_24px] opacity-10" />
        <div className="container relative z-10">
          <div className="mx-auto max-w-3xl text-center">
            <div className="inline-flex items-center gap-2 rounded-full border border-[#087F8C]/20 bg-[#DDF2F0] px-3.5 py-1 text-xs font-semibold text-[#087F8C] dark:bg-teal-950 dark:text-teal-300 dark:border-teal-800 mb-6">
              <Sparkles className="h-3.5 w-3.5" /> Dual-Stream Public Health Surveillance
            </div>

            <h1 className="text-4xl font-extrabold tracking-tight sm:text-5xl lg:text-6xl text-[#142B3B] dark:text-white leading-[1.15]">
              Connecting Civic Complaints with Community Health Signals
            </h1>

            <p className="mx-auto mt-6 max-w-2xl text-base text-[#71818A] dark:text-slate-300 leading-relaxed">
              HealthPulse AI bridges municipal environmental reporting with voluntary patient symptom records using explainable on-device NLP, identifying statistical co-occurrence anomalies before they escalate into public health crises.
            </p>

            <div className="mt-8 flex flex-wrap items-center justify-center gap-3">
              <Link href="/login">
                <Button size="lg" className="h-11 bg-[#087F8C] hover:bg-[#066873] text-white font-semibold text-xs px-6 shadow-sm">
                  Launch Platform (Demo Accounts) <ArrowRight className="h-4 w-4 ml-1.5" />
                </Button>
              </Link>
              <Link href="/register">
                <Button size="lg" variant="outline" className="h-11 border-[#E4EAE9] text-xs font-semibold hover:bg-[#F7F8F6] px-6 dark:border-slate-700">
                  Register as Citizen / Patient
                </Button>
              </Link>
            </div>

            {/* Live Stats Strip */}
            <div className="mt-14 grid gap-4 sm:grid-cols-3">
              <StatCard
                label="Total Civic Ingest"
                value={stats?.total_complaints ?? "100+"}
                hint="Analyzed with on-device NLP"
                icon={<Megaphone className="h-5 w-5" />}
              />
              <StatCard
                label="Resolution Rate"
                value={stats ? `${Math.round(stats.resolution_rate * 100)}%` : "92%"}
                hint={`${stats?.resolved_complaints ?? "80+"} remediated cases`}
                icon={<CheckCircle2 className="h-5 w-5 text-emerald-600" />}
              />
              <StatCard
                label="Monitored Districts"
                value={stats?.districts_covered ?? "6"}
                hint="Integrated municipal sectors"
                icon={<MapPin className="h-5 w-5 text-[#087F8C]" />}
              />
            </div>
          </div>
        </div>
      </section>

      {/* 4 Intelligence Engines Section */}
      <section id="platform" className="py-20 bg-[#F7F8F6] dark:bg-[#102330]">
        <div className="container">
          <div className="mx-auto max-w-2xl text-center">
            <span className="text-xs font-bold uppercase tracking-wider text-[#087F8C]">Platform Capabilities</span>
            <h2 className="mt-2 text-3xl font-bold tracking-tight text-[#142B3B] dark:text-white">
              Four Specialized Intelligence Engines
            </h2>
            <p className="mt-3 text-xs text-[#71818A] dark:text-slate-400">
              Designed from first principles for public health and civic operations — explainable, evidence-backed, and fully privacy preserving.
            </p>
          </div>

          <div className="mt-12 grid gap-6 md:grid-cols-2">
            {ENGINES.map((engine) => {
              const Icon = engine.icon;
              return (
                <Card
                  key={engine.title}
                  className="border-[#E4EAE9] bg-white shadow-subtle hover:shadow-card transition-shadow dark:border-slate-800 dark:bg-[#142B3B]"
                >
                  <CardContent className="p-7">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-[#DDF2F0] text-[#087F8C] dark:bg-teal-950 dark:text-teal-300">
                        <Icon className="h-5 w-5" />
                      </div>
                      <span className="rounded bg-[#F7F8F6] px-2.5 py-1 text-[11px] font-semibold text-[#203A4A] border border-[#E4EAE9] dark:bg-slate-800 dark:border-slate-700 dark:text-slate-300">
                        {engine.badge}
                      </span>
                    </div>

                    <h3 className="text-base font-bold text-[#192D38] dark:text-white mb-2">
                      {engine.title}
                    </h3>

                    <ul className="space-y-2 text-xs text-[#71818A] dark:text-slate-300">
                      {engine.points.map((point) => (
                        <li key={point} className="flex items-start gap-2">
                          <CheckCircle2 className="h-3.5 w-3.5 text-[#087F8C] shrink-0 mt-0.5" />
                          <span>{point}</span>
                        </li>
                      ))}
                    </ul>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* How the Pipeline Works */}
      <section id="how" className="py-20 border-y border-[#E4EAE9] bg-white dark:border-slate-800 dark:bg-[#142B3B]">
        <div className="container">
          <div className="mx-auto max-w-2xl text-center">
            <span className="text-xs font-bold uppercase tracking-wider text-[#087F8C]">Architecture</span>
            <h2 className="mt-2 text-3xl font-bold tracking-tight text-[#142B3B] dark:text-white">
              End-to-End Surveillance Pipeline
            </h2>
            <p className="mt-3 text-xs text-[#71818A] dark:text-slate-400">
              How natural language reports turn into actionable public health investigations without proprietary API dependencies.
            </p>
          </div>

          <div className="mt-12 grid gap-6 md:grid-cols-4">
            {[
              {
                step: "01",
                title: "Intake & NLP Extraction",
                desc: "Civic grievances and voluntary symptoms are normalized, geocoded, entity-tagged, and embedded into semantic vectors on-device.",
              },
              {
                step: "02",
                title: "Near-Duplicate Detection",
                desc: "Repeated citizen reports are matched against existing complaints to eliminate duplicate tickets while preserving incident severity weighting.",
              },
              {
                step: "03",
                title: "Cross-Domain Co-Occurrence",
                desc: "Spatial and temporal windows calculate pairwise semantic alignment and statistical lift between environmental hazards and symptom outbreaks.",
              },
              {
                step: "04",
                title: "Investigation & Closure",
                desc: "Correlated signals trigger evidence-backed alerts for public health officers and municipal teams to dispatch inspectors and log resolutions.",
              },
            ].map((s) => (
              <div
                key={s.step}
                className="relative rounded-lg border border-[#E4EAE9] bg-[#F7F8F6] p-6 dark:border-slate-800 dark:bg-slate-900/60"
              >
                <span className="font-mono text-3xl font-extrabold text-[#087F8C]/30 dark:text-teal-500/20">
                  {s.step}
                </span>
                <h3 className="mt-3 text-sm font-bold text-[#192D38] dark:text-white">
                  {s.title}
                </h3>
                <p className="mt-2 text-xs leading-relaxed text-[#71818A] dark:text-slate-400">
                  {s.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Stakeholders & Roles */}
      <section id="roles" className="py-20 bg-[#F7F8F6] dark:bg-[#102330]">
        <div className="container">
          <div className="mx-auto max-w-2xl text-center">
            <span className="text-xs font-bold uppercase tracking-wider text-[#087F8C]">Role-Based Architecture</span>
            <h2 className="mt-2 text-3xl font-bold tracking-tight text-[#142B3B] dark:text-white">
              Six Tailored Stakeholder Dashboards
            </h2>
            <p className="mt-3 text-xs text-[#71818A] dark:text-slate-400">
              Strict privacy boundaries ensure patient medical narratives remain anonymous while providing operations teams the exact telemetry they require.
            </p>
          </div>

          <div className="mt-12 grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {ROLES.map((r) => {
              const Icon = r.icon;
              return (
                <Card
                  key={r.title}
                  className="border-[#E4EAE9] bg-white shadow-subtle dark:border-slate-800 dark:bg-[#142B3B]"
                >
                  <CardContent className="p-6">
                    <div className="flex items-center justify-between mb-3">
                      <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-[#DDF2F0] text-[#087F8C] dark:bg-teal-950 dark:text-teal-300">
                        <Icon className="h-4.5 w-4.5" />
                      </div>
                      <span className="rounded bg-[#F7F8F6] px-2 py-0.5 text-[10px] font-semibold text-[#71818A] border border-[#E4EAE9] dark:bg-slate-800 dark:border-slate-700">
                        {r.tag}
                      </span>
                    </div>
                    <h3 className="text-sm font-bold text-[#192D38] dark:text-white">{r.title}</h3>
                    <p className="mt-2 text-xs leading-relaxed text-[#71818A] dark:text-slate-300">
                      {r.text}
                    </p>
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </div>
      </section>

      {/* Responsible AI Advisory */}
      <section id="ethics" className="py-16 border-t border-[#E4EAE9] bg-white dark:border-slate-800 dark:bg-[#142B3B]">
        <div className="container">
          <div className="rounded-xl border border-[#E4EAE9] bg-[#F7F8F6] p-8 dark:border-slate-800 dark:bg-slate-900/60">
            <div className="flex flex-col md:flex-row items-start gap-5">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-lg bg-[#DDF2F0] text-[#087F8C] dark:bg-teal-950 dark:text-teal-300">
                <ShieldCheck className="h-6 w-6" />
              </div>
              <div className="space-y-2">
                <h3 className="text-base font-bold text-[#142B3B] dark:text-white">
                  Responsible AI, Clinical Ethics & Legal Disclaimer
                </h3>
                <p className="text-xs leading-relaxed text-[#71818A] dark:text-slate-300">
                  HealthPulse AI is designed exclusively for epidemiological surveillance and municipal remediation workflow management. The system does not diagnose clinical illnesses, provide individualized medical treatment recommendations, or make automated causal claims. All cross-domain correlation alerts are statistical association signals intended to prioritize field investigations by certified public health officials.
                </p>
                <div className="flex flex-wrap gap-4 pt-1 text-[11px] font-medium text-[#087F8C] dark:text-teal-300">
                  <span>✓ De-identified patient records</span>
                  <span>✓ Auditable deterministic models</span>
                  <span>✓ Zero cloud leakage of health text</span>
                  <span>✓ Human-in-the-loop validation</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Footer */}
      <section className="py-16 bg-[#142B3B] text-white">
        <div className="container text-center">
          <h2 className="text-2xl font-bold tracking-tight sm:text-3xl">
            Explore the HealthPulse AI Platform
          </h2>
          <p className="mx-auto mt-3 max-w-xl text-xs text-[#9BB0BC] leading-relaxed">
            Test any of the 6 roles instantly using pre-seeded demonstration credentials verified through the FastAPI backend.
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Link href="/login">
              <Button size="lg" className="h-10 bg-[#087F8C] hover:bg-[#066873] text-white text-xs font-semibold px-6 shadow-sm">
                Open Demo Logins <ArrowRight className="h-3.5 w-3.5 ml-1.5" />
              </Button>
            </Link>
          </div>
        </div>
      </section>

      {/* Footer copyright */}
      <footer className="border-t border-[#E4EAE9] py-6 text-xs text-[#71818A] bg-white dark:border-slate-800 dark:bg-[#102330]">
        <div className="container flex flex-col items-center justify-between gap-3 sm:flex-row">
          <p>© 2026 HealthPulse AI Platform · All rights reserved.</p>
          <p className="flex items-center gap-1.5 text-[11px]">
            <Activity className="h-3.5 w-3.5 text-[#087F8C]" />
            Enterprise Healthcare & Civic Intelligence Framework
          </p>
        </div>
      </footer>
    </div>
  );
}
