import type { Citation } from "@/types";

export function CitationBlock({ citations }: { citations: Citation[] }) {
  if (!citations.length) return null;
  return (
    <div className="mt-4 rounded border border-sky-200 bg-sky-50 p-4">
      <p className="text-xs font-semibold uppercase tracking-wide text-sky-700">Sources</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {citations.map((citation) => (
          <span key={citation.chunk_id} className="rounded border border-sky-200 bg-white px-2 py-1 text-xs text-slate-700">
            Page {citation.page_number}, chunk {citation.chunk_index + 1}
          </span>
        ))}
      </div>
    </div>
  );
}
