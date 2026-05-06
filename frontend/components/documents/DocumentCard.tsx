import Link from "next/link";
import { FileText, MessageSquareText, NotebookPen } from "lucide-react";
import type { StudyDocument } from "@/types";
import { formatDate, statusClass } from "@/lib/utils";

export function DocumentCard({ document }: { document: StudyDocument }) {
  return (
    <article className="rounded-lg border border-study-line bg-white p-5 sm:p-6">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="flex items-start gap-2 text-study-navy">
            <FileText className="mt-0.5 shrink-0" size={18} />
            <h3 className="min-w-0 break-words font-semibold">{document.title}</h3>
          </div>
          <p className="mt-2 text-sm text-slate-500">
            {document.file_type} · {document.chunk_count} chunks · {formatDate(document.created_at)}
          </p>
        </div>
        <span className={`w-fit rounded border px-2 py-1 text-xs font-semibold uppercase ${statusClass(document.status)}`}>
          {document.status}
        </span>
      </div>
      {document.error_message ? <p className="mt-4 text-sm text-red-600">{document.error_message}</p> : null}
      <div className="mt-6 grid grid-cols-1 gap-2 sm:flex sm:flex-wrap">
        <Link href={`/documents/${document.id}`} className="rounded border border-study-line px-3 py-2 text-center text-sm font-medium text-study-navy hover:bg-slate-50 sm:text-left">
          Details
        </Link>
        <Link href={`/documents/${document.id}/ask`} className="inline-flex items-center justify-center gap-2 rounded border border-study-line px-3 py-2 text-sm font-medium text-study-navy hover:bg-slate-50 sm:justify-start">
          <MessageSquareText size={15} />
          Ask
        </Link>
        <Link href={`/documents/${document.id}/quizzes`} className="inline-flex items-center justify-center gap-2 rounded bg-study-navy px-3 py-2 text-sm font-semibold text-white hover:bg-black sm:justify-start">
          <NotebookPen size={15} />
          Quiz
        </Link>
      </div>
    </article>
  );
}
