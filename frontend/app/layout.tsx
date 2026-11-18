import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/lib/auth-context";
import { ThemeProvider } from "@/components/theme";
import { ToastProvider } from "@/components/ui/toast";

export const metadata: Metadata = {
  title: {
    default: "HealthPulse AI — Healthcare & Civic Intelligence Platform",
    template: "%s · HealthPulse AI",
  },
  description:
    "HealthPulse AI connects environmental complaints with voluntary symptom reports to surface potential community health concerns for investigation — with explainable, evidence-backed signals.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
  <html lang="en" suppressHydrationWarning>
      <body>
        <ThemeProvider>
          <AuthProvider>
            <ToastProvider>{children}</ToastProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
