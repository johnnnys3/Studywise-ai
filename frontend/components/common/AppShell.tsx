"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  BarChart3,
  BookOpen,
  BrainCircuit,
  FileText,
  Gauge,
  GraduationCap,
  Layers3,
  LogOut,
  Upload,
} from "lucide-react";
import { clearToken } from "@/lib/api";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: Gauge },
  { href: "/documents", label: "Documents", icon: FileText },
  { href: "/documents/upload", label: "Upload", icon: Upload },
  { href: "/quizzes", label: "Quizzes", icon: BookOpen },
  { href: "/progress", label: "Progress", icon: BarChart3 },
  { href: "/ai-pipeline", label: "AI Pipeline", icon: Layers3 },
  { href: "/evaluation", label: "Evaluation", icon: BrainCircuit },
];

export function AppShell({ children, title }: { children: React.ReactNode; title: string }) {
  const pathname = usePathname();
  const router = useRouter();

  function logout() {
    clearToken();
    router.push("/auth/login");
  }

  return (
    <div className="min-h-screen bg-study-surface">
      <aside className="fixed inset-y-0 left-0 hidden w-64 border-r border-study-line bg-white px-4 py-5 lg:block">
        <Link href="/" className="flex items-center gap-3 px-2">
          <span className="grid h-9 w-9 place-items-center rounded bg-study-navy text-white">
            <GraduationCap size={20} />
          </span>
          <span>
            <span className="block text-sm font-semibold text-study-navy">StudyWise AI</span>
            <span className="block text-xs text-slate-500">Academic Precision</span>
          </span>
        </Link>
        <nav className="mt-8 space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={`flex items-center gap-3 rounded px-3 py-2 text-sm font-medium ${
                  active ? "bg-slate-100 text-study-navy" : "text-slate-600 hover:bg-slate-50 hover:text-study-navy"
                }`}
              >
                <Icon size={18} strokeWidth={1.6} />
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>

      <div className="lg:pl-64">
        <header className="sticky top-0 z-10 border-b border-study-line bg-white/95 backdrop-blur">
          <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-5">
            <h1 className="text-lg font-semibold text-study-navy">{title}</h1>
            <button
              type="button"
              onClick={logout}
              className="inline-flex items-center gap-2 rounded border border-study-line px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-50"
            >
              <LogOut size={16} />
              Logout
            </button>
          </div>
        </header>
        <main className="mx-auto max-w-7xl px-5 py-8">{children}</main>
      </div>
    </div>
  );
}
