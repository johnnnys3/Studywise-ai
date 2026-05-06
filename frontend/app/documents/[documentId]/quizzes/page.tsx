"use client";

import { FormEvent, useState } from "react";
import { useParams } from "next/navigation";
import { AppShell } from "@/components/common/AppShell";
import { PageHeader } from "@/components/common/PageHeader";
import { api } from "@/lib/api";
import type { Quiz, QuizAttempt } from "@/types";

export default function DocumentQuizPage() {
  const params = useParams<{ documentId: string }>();
  const [questionCount, setQuestionCount] = useState(5);
  const [difficulty, setDifficulty] = useState("medium");
  const [quiz, setQuiz] = useState<Quiz | null>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [attempt, setAttempt] = useState<QuizAttempt | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function createQuiz(event: FormEvent) {
    event.preventDefault();
    setError("");
    setAttempt(null);
    setLoading(true);
    try {
      setQuiz(await api.createQuiz(params.documentId, questionCount, difficulty));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Quiz generation failed.");
    } finally {
      setLoading(false);
    }
  }

  async function submitQuiz() {
    if (!quiz) return;
    setError("");
    try {
      setAttempt(await api.submitQuiz(quiz.id, answers));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Quiz submission failed.");
    }
  }

  return (
    <AppShell title="Quizzes & Flashcards">
      <PageHeader
        eyebrow="Practice"
        title="Generate a document quiz"
        description="Create a multiple-choice quiz, submit your answers, and update weak topics from the score."
      />
      <form onSubmit={createQuiz} className="flex flex-col gap-4 rounded-lg border border-study-line bg-white p-5 md:flex-row md:items-end">
        <label className="text-sm font-medium text-study-navy md:w-36">
          Questions
          <input type="number" min={1} max={20} value={questionCount} onChange={(event) => setQuestionCount(Number(event.target.value))} className="mt-2 block w-full rounded border border-study-line px-3 py-2" />
        </label>
        <label className="text-sm font-medium text-study-navy md:w-44">
          Difficulty
          <select value={difficulty} onChange={(event) => setDifficulty(event.target.value)} className="mt-2 block w-full rounded border border-study-line px-3 py-2">
            <option value="easy">Easy</option>
            <option value="medium">Medium</option>
            <option value="hard">Hard</option>
          </select>
        </label>
        <button disabled={loading} className="rounded bg-study-navy px-5 py-2.5 text-sm font-semibold text-white hover:bg-black disabled:opacity-60 md:w-auto">
          {loading ? "Generating..." : "Generate quiz"}
        </button>
      </form>
      {error ? <p className="mt-5 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
      {attempt ? (
        <div className="mt-6 rounded-lg border border-emerald-200 bg-emerald-50 p-5">
          <p className="text-lg font-semibold text-emerald-800">Score: {attempt.score}/{attempt.total_questions} ({attempt.percentage}%)</p>
        </div>
      ) : null}
      {quiz ? (
        <section className="mt-8 space-y-5">
          {quiz.questions.map((question, index) => (
            <article key={question.id} className="rounded-lg border border-study-line bg-white p-5 sm:p-6">
              <p className="text-sm font-semibold text-slate-500">Question {index + 1} · {question.topic} · Page {question.source_page}</p>
              <h2 className="mt-2 font-semibold text-study-navy">{question.question}</h2>
              <div className="mt-4 grid gap-2">
                {question.options_json.map((option) => (
                  <label key={option} className="flex items-start gap-3 rounded border border-study-line p-3 text-sm text-slate-700 hover:bg-slate-50">
                    <input className="mt-0.5 shrink-0" type="radio" name={question.id} value={option} checked={answers[question.id] === option} onChange={() => setAnswers((current) => ({ ...current, [question.id]: option }))} />
                    {option}
                  </label>
                ))}
              </div>
              {attempt ? <p className="reading-copy mt-4 rounded bg-slate-50 p-4 text-slate-700">{question.explanation}</p> : null}
            </article>
          ))}
          <button onClick={submitQuiz} className="w-full rounded bg-study-navy px-5 py-2.5 text-sm font-semibold text-white hover:bg-black sm:w-auto">Submit answers</button>
        </section>
      ) : null}
    </AppShell>
  );
}
