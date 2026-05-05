"use client";

import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { FormEvent, Suspense, useState } from "react";
import { api, setToken } from "@/lib/api";

export default function LoginPage() {
  return (
    <Suspense fallback={<LoginFallback />}>
      <LoginForm />
    </Suspense>
  );
}

function LoginFallback() {
  return <main className="min-h-screen bg-study-surface" />;
}

function LoginForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [name, setName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const sessionExpired = searchParams.get("session") === "expired";

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const response = await api.login({ name, password });
      setToken(response.access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-study-surface px-5">
      <form onSubmit={submit} className="w-full max-w-md rounded-lg border border-study-line bg-white p-8">
        <Link href="/" className="text-sm font-semibold text-study-navy">StudyWise AI</Link>
        <h1 className="mt-6 text-3xl font-semibold text-study-navy">Log in</h1>
        <p className="mt-2 text-sm text-slate-600">Access your documents, quizzes, and progress.</p>
        {sessionExpired && !error ? (
          <p className="mt-5 rounded border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
            Your session expired. Please log in again.
          </p>
        ) : null}
        {error ? <p className="mt-5 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        <label className="mt-6 block text-sm font-medium text-study-navy">
          Name
          <input className="mt-2 w-full rounded border border-study-line px-3 py-2 outline-none focus:border-study-navy" value={name} onChange={(event) => setName(event.target.value)} required />
        </label>
        <label className="mt-4 block text-sm font-medium text-study-navy">
          Password
          <input className="mt-2 w-full rounded border border-study-line px-3 py-2 outline-none focus:border-study-navy" value={password} onChange={(event) => setPassword(event.target.value)} type="password" required />
        </label>
        <button disabled={loading} className="mt-6 w-full rounded bg-study-navy px-4 py-2.5 text-sm font-semibold text-white hover:bg-black disabled:opacity-60">
          {loading ? "Logging in..." : "Log in"}
        </button>
        <p className="mt-5 text-center text-sm text-slate-600">
          New here? <Link href="/auth/register" className="font-semibold text-study-navy">Create an account</Link>
        </p>
      </form>
    </main>
  );
}
