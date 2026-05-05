"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/common/AppShell";
import { EmptyState } from "@/components/common/EmptyState";
import { PageHeader } from "@/components/common/PageHeader";
import { api } from "@/lib/api";
import type { Quiz } from "@/types";

export default function QuizzesPage() {
  const [quizzes, setQuizzes] = useState<Quiz[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api.quizzes().then(setQuizzes).catch((err) => setError(err instanceof Error ? err.message : "Could not load quizzes."));
  }, []);

  return (
    <AppShell title="Quizzes">
      <PageHeader eyebrow="Practice history" title="Generated quizzes" description="Review quizzes generated from uploaded documents." />
      {error ? <p className="mb-6 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
      {quizzes.length ? (
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          {quizzes.map((quiz) => (
            <article key={quiz.id} className="rounded-lg border border-study-line bg-white p-6">
              <h2 className="font-semibold text-study-navy">{quiz.title}</h2>
              <p className="mt-2 text-sm text-slate-500">{quiz.difficulty} · {quiz.questions.length} questions</p>
              <Link href={`/documents/${quiz.document_id}/quizzes`} className="mt-5 inline-flex rounded border border-study-line px-3 py-2 text-sm font-semibold text-study-navy hover:bg-slate-50">Retake from document</Link>
            </article>
          ))}
        </div>
      ) : (
        <EmptyState title="No quizzes yet" description="Open a processed document and generate a practice quiz." href="/documents" actionLabel="Choose document" />
      )}
    </AppShell>
  );
}
