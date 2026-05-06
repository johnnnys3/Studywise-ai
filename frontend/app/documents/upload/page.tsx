"use client";

import { UploadCloud } from "lucide-react";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { AppShell } from "@/components/common/AppShell";
import { PageHeader } from "@/components/common/PageHeader";
import { api } from "@/lib/api";

export default function UploadDocumentPage() {
  const router = useRouter();
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!file) {
      setError("Choose a PDF or TXT file first.");
      return;
    }
    setError("");
    setLoading(true);
    try {
      const document = await api.uploadDocument(file);
      router.push(`/documents/${document.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell title="Upload Document">
      <PageHeader
        eyebrow="Document ingestion"
        title="Upload learning material"
        description="The MVP accepts PDF and TXT files up to 10MB. Text is extracted, chunked, and made available for cited answers and quizzes."
      />
      <form onSubmit={submit} className="rounded-lg border border-study-line bg-white p-5 sm:p-8">
        <label className="grid cursor-pointer place-items-center rounded-lg border border-dashed border-slate-300 bg-slate-50 px-4 py-10 text-center hover:bg-white sm:px-6 sm:py-16">
          <UploadCloud className="text-study-accent" size={36} />
          <span className="mt-4 block max-w-full break-words text-base font-semibold text-study-navy sm:text-lg">{file ? file.name : "Choose a PDF or TXT file"}</span>
          <span className="mt-2 block text-sm text-slate-500">Supported: PDF, TXT · Max 10MB</span>
          <input className="sr-only" type="file" accept=".pdf,.txt,application/pdf,text/plain" onChange={(event) => setFile(event.target.files?.[0] ?? null)} />
        </label>
        {error ? <p className="mt-5 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        <button disabled={loading} className="mt-6 w-full rounded bg-study-navy px-5 py-2.5 text-sm font-semibold text-white hover:bg-black disabled:opacity-60 sm:w-auto">
          {loading ? "Processing..." : "Upload and process"}
        </button>
      </form>
    </AppShell>
  );
}
