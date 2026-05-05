import Link from "next/link";
import { FileText, MessageSquareText, NotebookPen } from "lucide-react";
import type { StudyDocument } from "@/types";
import { formatDate, statusClass } from "@/lib/utils";

export function DocumentCard({ document }: { document: StudyDocument }) {
  return (
    <article className="rounded-lg border border-study-line bg-white p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-study-navy">
            <FileText size={18} />
            <h3 className="font-semibold">{document.title}</h3>
          </div>
          <p className="mt-2 text-sm text-slate-500">
            {document.file_type} · {document.chunk_count} chunks · {formatDate(document.created_at)}
          </p>
        </div>
        <span className={`rounded border px-2 py-1 text-xs font-semibold uppercase ${statusClass(document.status)}`}>
          {document.status}
        </span>
      </div>
      {document.error_message ? <p className="mt-4 text-sm text-red-600">{document.error_message}</p> : null}
      <div className="mt-6 flex flex-wrap gap-2">
        <Link href={`/documents/${document.id}`} className="rounded border border-study-line px-3 py-2 text-sm font-medium text-study-navy hover:bg-slate-50">
          Details
        </Link>
        <Link href={`/documents/${document.id}/ask`} className="inline-flex items-center gap-2 rounded border border-study-line px-3 py-2 text-sm font-medium text-study-navy hover:bg-slate-50">
          <MessageSquareText size={15} />
          Ask
        </Link>
        <Link href={`/documents/${document.id}/quizzes`} className="inline-flex items-center gap-2 rounded bg-study-navy px-3 py-2 text-sm font-semibold text-white hover:bg-black">
          <NotebookPen size={15} />
          Quiz
        </Link>
      </div>
    </article>
  );
}
