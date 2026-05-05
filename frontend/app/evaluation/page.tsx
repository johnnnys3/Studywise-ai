"use client";

import { useEffect, useState } from "react";
import { AppShell } from "@/components/common/AppShell";
import { PageHeader } from "@/components/common/PageHeader";
import { api } from "@/lib/api";

export default function EvaluationPage() {
  const [metrics, setMetrics] = useState<{ metric_name: string; metric_value: number }[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    api.evaluation()
      .then(setMetrics)
      .catch((err) => setError(err instanceof Error ? err.message : "Could not load metrics."));
  }, []);

  return (
    <AppShell title="Evaluation">
      <PageHeader
        eyebrow="AI quality"
        title="Evaluation dashboard"
        description="Track retrieval quality, citation coverage, latency, and structured generation reliability."
      />
      {error ? <p className="mb-6 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-5">
        {metrics.map((metric) => (
          <article key={metric.metric_name} className="rounded-lg border border-study-line bg-white p-5">
            <p className="text-sm font-medium capitalize text-slate-500">{metric.metric_name.replaceAll("_", " ")}</p>
            <p className="mt-3 text-3xl font-semibold text-study-navy">{metric.metric_value}</p>
          </article>
        ))}
      </div>
    </AppShell>
  );
}
