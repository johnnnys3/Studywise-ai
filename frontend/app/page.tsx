import Link from "next/link";
import { ArrowRight, BarChart3, FileText, MessageSquareText, NotebookTabs } from "lucide-react";

const features = [
  { title: "Upload materials", description: "Add PDFs or TXT notes and process them into searchable study chunks.", icon: FileText },
  { title: "Ask cited questions", description: "Get answers grounded in your own material with page and chunk references.", icon: MessageSquareText },
  { title: "Generate quizzes", description: "Create multiple-choice quizzes from documents and review explanations.", icon: NotebookTabs },
  { title: "Track weak topics", description: "Use quiz results to find topics that need more review.", icon: BarChart3 },
];

export default function HomePage() {
  return (
    <main className="min-h-screen bg-study-surface">
      <header className="border-b border-study-line bg-white">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between gap-3 px-4 sm:px-5">
          <Link href="/" className="font-semibold text-study-navy">StudyWise AI</Link>
          <div className="flex shrink-0 items-center gap-3">
            <Link href="/auth/login" className="text-sm font-medium text-slate-600 hover:text-study-navy">Log in</Link>
            <Link href="/auth/register" className="rounded bg-study-navy px-3 py-2 text-sm font-semibold text-white hover:bg-black sm:px-4">Get started</Link>
          </div>
        </div>
      </header>

      <section className="mx-auto grid max-w-7xl grid-cols-1 gap-8 px-4 py-10 sm:px-5 sm:py-14 lg:min-h-[calc(100vh-64px)] lg:grid-cols-[1.1fr_0.9fr] lg:items-center lg:gap-12 lg:py-16">
        <div>
          <p className="text-sm font-semibold uppercase tracking-wide text-study-accent">Citation-backed study assistant</p>
          <h1 className="mt-4 max-w-4xl text-3xl font-semibold leading-tight text-study-navy sm:text-4xl lg:text-5xl">
            Turn your study materials into answers, quizzes, flashcards, and progress insights.
          </h1>
          <p className="reading-copy mt-5 max-w-2xl text-lg text-slate-700 sm:mt-6 sm:text-xl">
            StudyWise AI grounds responses in uploaded documents, then helps students review, test, and improve weak topics over time.
          </p>
          <div className="mt-8 grid grid-cols-1 gap-3 sm:flex sm:flex-wrap">
            <Link href="/auth/register" className="inline-flex items-center justify-center gap-2 rounded bg-study-navy px-5 py-3 text-sm font-semibold text-white hover:bg-black">
              Start studying <ArrowRight size={16} />
            </Link>
            <Link href="/ai-pipeline" className="rounded border border-study-line bg-white px-5 py-3 text-center text-sm font-semibold text-study-navy hover:bg-slate-50">
              View RAG pipeline
            </Link>
          </div>
        </div>

        <div className="rounded-lg border border-study-line bg-white p-5 shadow-academic sm:p-6">
          <div className="border-b border-study-line pb-4">
            <p className="text-sm font-semibold text-study-navy">Document Q&A</p>
            <p className="mt-1 text-sm text-slate-500">Grounded answer preview</p>
          </div>
          <div className="mt-5 space-y-4">
            <div className="rounded bg-slate-50 p-4">
              <p className="text-sm font-medium text-slate-600">Question</p>
              <p className="mt-2 text-study-navy">What does retrieval-augmented generation improve?</p>
            </div>
            <div className="rounded border border-sky-200 bg-sky-50 p-4">
              <p className="reading-copy text-slate-800">
                RAG improves answer grounding by retrieving relevant document chunks before generation, reducing generic or unsupported responses.
              </p>
              <div className="mt-4 flex gap-2">
                <span className="rounded border border-sky-200 bg-white px-2 py-1 text-xs text-slate-700">Page 3</span>
                <span className="rounded border border-sky-200 bg-white px-2 py-1 text-xs text-slate-700">Chunk 4</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="border-t border-study-line bg-white py-10 sm:py-14">
        <div className="mx-auto grid max-w-7xl grid-cols-1 gap-4 px-4 sm:px-5 md:grid-cols-2 lg:grid-cols-4">
          {features.map((feature) => {
            const Icon = feature.icon;
            return (
              <article key={feature.title} className="rounded-lg border border-study-line p-5">
                <Icon className="text-study-accent" size={22} />
                <h2 className="mt-4 font-semibold text-study-navy">{feature.title}</h2>
                <p className="mt-2 text-sm leading-6 text-slate-600">{feature.description}</p>
              </article>
            );
          })}
        </div>
      </section>
    </main>
  );
}
