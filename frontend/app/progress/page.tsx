"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/common/AppShell";
import { PageHeader } from "@/components/common/PageHeader";
import { StatCard } from "@/components/common/StatCard";
import { WeakTopicCard } from "@/components/progress/WeakTopicCard";
import { api } from "@/lib/api";
import type { ProgressSummary, WeakTopic } from "@/types";

export default function ProgressPage() {
  const [summary, setSummary] = useState<ProgressSummary | null>(null);
  const [topics, setTopics] = useState<WeakTopic[]>([]);
  const [recommendations, setRecommendations] = useState<{ topic: string; message: string; priority: string }[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    Promise.all([api.progressSummary(), api.weakTopics(), api.recommendations()])
      .then(([summaryResponse, topicResponse, recommendationResponse]) => {
        setSummary(summaryResponse);
        setTopics(topicResponse);
        setRecommendations(recommendationResponse);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load progress."));
  }, []);

  return (
    <AppShell title="Learning Progress">
      <PageHeader
        eyebrow="Performance"
        title="Track weak topics"
        description="Quiz attempts update topic-level accuracy and create review recommendations."
      />
      {error ? <p className="mb-6 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
      <section className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <StatCard label="Average score" value={`${summary?.average_quiz_score ?? 0}%`} />
        <StatCard label="Completed quizzes" value={summary?.quizzes_completed ?? 0} />
        <StatCard label="Weak topics" value={summary?.weak_topic_count ?? 0} />
      </section>
      <section className="mt-10 grid grid-cols-1 gap-6 lg:grid-cols-[1.2fr_0.8fr]">
        <div>
          <h2 className="mb-4 text-xl font-semibold text-study-navy">Topic accuracy</h2>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {topics.length ? topics.map((topic) => <WeakTopicCard key={topic.id} topic={topic} />) : <p className="text-sm text-slate-500">Submit a quiz to populate weak topics.</p>}
          </div>
        </div>
        <div className="rounded-lg border border-study-line bg-white p-6">
          <h2 className="font-semibold text-study-navy">Review recommendations</h2>
          <div className="mt-4 space-y-3">
            {recommendations.length ? recommendations.map((recommendation) => (
              <article key={recommendation.topic} className="rounded border border-study-line bg-slate-50 p-4">
                <p className="text-sm font-semibold text-study-navy">{recommendation.topic}</p>
                <p className="mt-1 text-sm leading-6 text-slate-600">{recommendation.message}</p>
              </article>
            )) : <p className="text-sm text-slate-500">No recommendations yet.</p>}
          </div>
        </div>
      </section>
    </AppShell>
  );
}
