"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import { AppShell } from "@/components/common/AppShell";
import { EmptyState } from "@/components/common/EmptyState";
import { PageHeader } from "@/components/common/PageHeader";
import { DocumentCard } from "@/components/documents/DocumentCard";
import { api } from "@/lib/api";
import type { StudyDocument } from "@/types";

export default function DocumentsPage() {
  const [documents, setDocuments] = useState<StudyDocument[]>([]);
  const [query, setQuery] = useState("");
  const [error, setError] = useState("");

  useEffect(() => {
    api.documents()
      .then(setDocuments)
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load documents."));
  }, []);

  const filteredDocuments = useMemo(
    () => documents.filter((document) => document.title.toLowerCase().includes(query.toLowerCase())),
    [documents, query],
  );

  const handleDelete = (documentId: string) => {
    setError("");
    api.deleteDocument(documentId)
      .then(() => setDocuments((current) => current.filter((document) => document.id !== documentId)))
      .catch((err) => setError(err instanceof Error ? err.message : "Could not delete document."));
  };

  return (
    <AppShell title="Documents">
      <PageHeader
        eyebrow="Knowledge base"
        title="Uploaded materials"
        description="Manage processed study files and open each document for cited Q&A, quizzes, and flashcards."
        action={<Link href="/documents/upload" className="rounded bg-study-navy px-4 py-2 text-sm font-semibold text-white hover:bg-black">Upload</Link>}
      />
      <input
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Search documents by title"
        className="mb-6 w-full rounded border border-study-line bg-white px-3 py-2 outline-none focus:border-study-navy"
      />
      {error ? <p className="mb-6 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
      {filteredDocuments.length ? (
        <div className="grid grid-cols-1 gap-4 xl:grid-cols-2">
          {filteredDocuments.map((document) => (
            <DocumentCard key={document.id} document={document} onDelete={handleDelete} />
          ))}
        </div>
      ) : (
        <EmptyState title="No matching documents" description="Upload a readable PDF or TXT file to begin building your study workspace." href="/documents/upload" actionLabel="Upload document" />
      )}
    </AppShell>
  );
}
