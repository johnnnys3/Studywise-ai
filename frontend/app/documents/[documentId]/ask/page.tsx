"use client";

import { FormEvent, useState } from "react";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/common/AppShell";
import { PageHeader } from "@/components/common/PageHeader";
import { CitationBlock } from "@/components/chat/CitationBlock";
import { api } from "@/lib/api";
import type { AskResponse } from "@/types";

export default function AskDocumentPage() {
  const params = useParams<{ documentId: string }>();
  const [question, setQuestion] = useState("");
  const [responses, setResponses] = useState<{ question: string; response: AskResponse }[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    if (!question.trim()) return;
    const askedQuestion = question.trim();
    setError("");
    setLoading(true);
    try {
      const response = await api.ask(params.documentId, askedQuestion);
      setResponses((current) => [{ question: askedQuestion, response }, ...current]);
      setQuestion("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Answer generation failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <AppShell title="Ask AI Assistant">
      <PageHeader
        eyebrow="Grounded Q&A"
        title="Ask citation-backed questions"
        description="The assistant retrieves relevant chunks from the selected document and answers only from that context."
      />
      <form onSubmit={submit} className="rounded-lg border border-study-line bg-white p-5">
        <label className="block text-sm font-medium text-study-navy">
          Question
          <textarea
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            rows={4}
            placeholder="Ask a question about this document..."
            className="mt-2 w-full resize-none rounded border border-study-line px-3 py-2 outline-none focus:border-study-navy"
          />
        </label>
        {error ? <p className="mt-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        <button disabled={loading} className="mt-4 rounded bg-study-navy px-5 py-2.5 text-sm font-semibold text-white hover:bg-black disabled:opacity-60">
          {loading ? "Retrieving..." : "Ask document"}
        </button>
      </form>

      <section className="mt-8 space-y-5">
        {responses.length ? responses.map((item) => (
          <article key={item.question} className="rounded-lg border border-study-line bg-white p-6">
            <p className="text-sm font-semibold text-slate-500">Question</p>
            <p className="mt-2 text-study-navy">{item.question}</p>
            <p className="reading-copy mt-5 text-lg text-slate-800">{item.response.answer}</p>
            <CitationBlock citations={item.response.citations} />
            <details className="mt-4 rounded border border-study-line bg-slate-50 p-4">
              <summary className="cursor-pointer text-sm font-semibold text-study-navy">Retrieved context</summary>
              <div className="mt-3 space-y-3">
                {item.response.retrieved_context.map((chunk) => (
                  <p key={chunk.id} className="reading-copy text-sm text-slate-600">
                    Page {chunk.page_number}: {chunk.chunk_text.slice(0, 420)}
                  </p>
                ))}
              </div>
            </details>
          </article>
        )) : (
          <div className="rounded-lg border border-study-line bg-white p-6">
            <p className="font-semibold text-study-navy">Suggested questions</p>
            <div className="mt-4 flex flex-wrap gap-2">
              {["Summarize the main idea.", "What should I review first?", "Create three study questions."].map((suggestion) => (
                <button key={suggestion} type="button" onClick={() => setQuestion(suggestion)} className="rounded border border-study-line px-3 py-2 text-sm text-slate-700 hover:bg-slate-50">
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        )}
      </section>
    </AppShell>
  );
}
