"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { AppShell } from "@/components/common/AppShell";
import { PageHeader } from "@/components/common/PageHeader";
import { api } from "@/lib/api";
import { statusClass } from "@/lib/utils";
import type { StudyDocument } from "@/types";

export default function DocumentDetailPage() {
  const params = useParams<{ documentId: string }>();
  const router = useRouter();
  const [document, setDocument] = useState<StudyDocument | null>(null);
  const [error, setError] = useState("");
  const [deleting, setDeleting] = useState(false);

  useEffect(() => {
    api.document(params.documentId)
      .then(setDocument)
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load document."));
  }, [params.documentId]);

  const handleDelete = () => {
    if (!document) return;
    if (!window.confirm(`Delete "${document.title}"? This removes its chunks, quizzes, and chat history.`)) return;
    setDeleting(true);
    setError("");
    api.deleteDocument(document.id)
      .then(() => router.push("/documents"))
      .catch((err) => {
        setError(err instanceof Error ? err.message : "Could not delete document.");
        setDeleting(false);
      });
  };

  return (
    <AppShell title="Document Details">
      <PageHeader
        eyebrow="Source material"
        title={document?.title ?? "Document"}
        description="Check processing status, inspect source chunks, and launch document-specific study actions."
      />
      {error ? <p className="rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
      {document ? (
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-[0.8fr_1.2fr]">
          <section className="rounded-lg border border-study-line bg-white p-5 sm:p-6">
            <span className={`rounded border px-2 py-1 text-xs font-semibold uppercase ${statusClass(document.status)}`}>{document.status}</span>
            <dl className="mt-6 space-y-4 text-sm">
              <div><dt className="font-medium text-slate-500">Original file</dt><dd className="mt-1 break-words text-study-navy">{document.original_filename}</dd></div>
              <div><dt className="font-medium text-slate-500">Pages</dt><dd className="mt-1 text-study-navy">{document.total_pages}</dd></div>
              <div><dt className="font-medium text-slate-500">Chunks</dt><dd className="mt-1 text-study-navy">{document.chunk_count}</dd></div>
            </dl>
            <div className="mt-6 grid grid-cols-1 gap-2 sm:flex sm:flex-wrap">
              <Link href={`/documents/${document.id}/ask`} className="rounded bg-study-navy px-4 py-2 text-center text-sm font-semibold text-white hover:bg-black sm:text-left">Ask AI</Link>
              <Link href={`/documents/${document.id}/quizzes`} className="rounded border border-study-line px-4 py-2 text-center text-sm font-semibold text-study-navy hover:bg-slate-50 sm:text-left">Generate quiz</Link>
              <Link href={`/documents/${document.id}/flashcards`} className="rounded border border-study-line px-4 py-2 text-center text-sm font-semibold text-study-navy hover:bg-slate-50 sm:text-left">Flashcards</Link>
              <button
                type="button"
                onClick={handleDelete}
                disabled={deleting}
                className="rounded border border-red-200 px-4 py-2 text-center text-sm font-semibold text-red-600 hover:bg-red-50 disabled:opacity-50 sm:text-left"
              >
                {deleting ? "Deleting..." : "Delete document"}
              </button>
            </div>
          </section>
          <section className="rounded-lg border border-study-line bg-white p-5 sm:p-6">
            <h2 className="font-semibold text-study-navy">Source chunk preview</h2>
            <div className="mt-4 space-y-4">
              {document.chunks?.length ? document.chunks.map((chunk) => (
                <article key={chunk.id} className="rounded border border-study-line bg-slate-50 p-4">
                  <p className="text-xs font-semibold uppercase text-slate-500">Page {chunk.page_number} · Chunk {chunk.chunk_index + 1}</p>
                  <p className="reading-copy mt-2 line-clamp-4 text-slate-700">{chunk.chunk_text}</p>
                </article>
              )) : <p className="text-sm text-slate-500">No chunks available yet.</p>}
            </div>
          </section>
        </div>
      ) : null}
    </AppShell>
  );
}
