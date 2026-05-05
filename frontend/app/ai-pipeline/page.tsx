import { AppShell } from "@/components/common/AppShell";
import { PageHeader } from "@/components/common/PageHeader";

const steps = [
  "PDF or TXT Upload",
  "Text Extraction",
  "Cleaning and Chunking",
  "Embedding Generation",
  "Vector Search",
  "LLM Answer",
  "Cited Response",
];

export default function AiPipelinePage() {
  return (
    <AppShell title="AI Pipeline">
      <PageHeader
        eyebrow="RAG internals"
        title="How StudyWise answers stay grounded"
        description="The MVP separates uploaded document content from system instructions, retrieves relevant chunks, and cites the source metadata used for each answer."
      />
      <section className="rounded-lg border border-study-line bg-white p-6">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-7">
          {steps.map((step, index) => (
            <div key={step} className="rounded border border-study-line bg-slate-50 p-4 text-center">
              <p className="text-xs font-semibold uppercase text-study-accent">Step {index + 1}</p>
              <p className="mt-2 text-sm font-semibold text-study-navy">{step}</p>
            </div>
          ))}
        </div>
      </section>
      <section className="mt-8 grid grid-cols-1 gap-4 lg:grid-cols-3">
        <article className="rounded-lg border border-study-line bg-white p-6">
          <h2 className="font-semibold text-study-navy">Retrieval scope</h2>
          <p className="mt-3 text-sm leading-6 text-slate-600">Search is filtered by current user and selected document, preventing cross-user or cross-document leakage.</p>
        </article>
        <article className="rounded-lg border border-study-line bg-white p-6">
          <h2 className="font-semibold text-study-navy">Prompt rule</h2>
          <p className="mt-3 text-sm leading-6 text-slate-600">If retrieved context is not enough, the assistant must say it cannot find enough information in the uploaded document.</p>
        </article>
        <article className="rounded-lg border border-study-line bg-white p-6">
          <h2 className="font-semibold text-study-navy">Citation metadata</h2>
          <p className="mt-3 text-sm leading-6 text-slate-600">Each answer can cite page number, chunk index, document ID, and chunk ID from stored source metadata.</p>
        </article>
      </section>
    </AppShell>
  );
}
