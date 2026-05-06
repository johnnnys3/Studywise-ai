"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/common/AppShell";
import { EmptyState } from "@/components/common/EmptyState";
import { PageHeader } from "@/components/common/PageHeader";
import { StatCard } from "@/components/common/StatCard";
import { DocumentCard } from "@/components/documents/DocumentCard";
import { api } from "@/lib/api";
import type { ProgressSummary, StudyDocument } from "@/types";

export default function DashboardPage() {
  const [summary, setSummary] = useState<ProgressSummary | null>(null);
  const [documents, setDocuments] = useState<StudyDocument[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.progressSummary(), api.documents()])
      .then(([summaryResponse, documentResponse]) => {
        setSummary(summaryResponse);
        setDocuments(documentResponse.slice(0, 3));
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load dashboard."));
  }, []);

  return (
    <AppShell title="Dashboard">
      <PageHeader
        eyebrow="Study workspace"
        title="Continue studying"
        description="Review recent documents, generate practice, and track weak areas from one focused dashboard."
        action={<Link href="/documents/upload" className="rounded bg-study-navy px-4 py-2 text-sm font-semibold text-white hover:bg-black">Upload document</Link>}
      />
      {error ? <p className="mb-6 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
      <section className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Documents" value={summary?.total_documents ?? 0} note="Uploaded materials" />
        <StatCard label="Quizzes completed" value={summary?.quizzes_completed ?? 0} note="Submitted attempts" />
        <StatCard label="Average score" value={`${summary?.average_quiz_score ?? 0}%`} note="Across completed quizzes" />
        <StatCard label="Weak topics" value={summary?.weak_topic_count ?? 0} note="Below target accuracy" />
      </section>
      <section className="mt-10">
        <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <h2 className="text-xl font-semibold text-study-navy">Recent documents</h2>
          <Link href="/documents" className="text-sm font-semibold text-study-navy">View all</Link>
        </div>
        {documents.length ? (
          <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
            {documents.map((document) => <DocumentCard key={document.id} document={document} />)}
          </div>
        ) : (
          <EmptyState title="No documents yet" description="Upload a PDF or TXT file to create citations, quizzes, flashcards, and progress insights." href="/documents/upload" actionLabel="Upload first document" />
        )}
      </section>
    </AppShell>
  );
}
