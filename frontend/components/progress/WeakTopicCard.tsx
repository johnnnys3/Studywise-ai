import type { WeakTopic } from "@/types";

export function WeakTopicCard({ topic }: { topic: WeakTopic }) {
  return (
    <div className="rounded-lg border border-study-line bg-white p-5">
      <div className="flex items-start justify-between gap-3">
        <h3 className="min-w-0 break-words font-semibold text-study-navy">{topic.topic}</h3>
        <span className="shrink-0 text-sm font-semibold text-slate-600">{topic.accuracy}%</span>
      </div>
      <div className="mt-4 h-2 rounded bg-slate-100">
        <div className="h-2 rounded bg-study-accent" style={{ width: `${Math.max(4, topic.accuracy)}%` }} />
      </div>
      <p className="mt-3 text-sm text-slate-500">
        {topic.correct_count} correct · {topic.incorrect_count} incorrect
      </p>
    </div>
  );
}
