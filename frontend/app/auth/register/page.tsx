"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";
import { api, setToken } from "@/lib/api";

export default function RegisterPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const response = await api.register({ name, email, password });
      setToken(response.access_token);
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-study-surface px-4 py-8 sm:px-5">
      <form onSubmit={submit} className="w-full max-w-md rounded-lg border border-study-line bg-white p-6 sm:p-8">
        <Link href="/" className="text-sm font-semibold text-study-navy">StudyWise AI</Link>
        <h1 className="mt-6 text-3xl font-semibold text-study-navy">Create account</h1>
        <p className="mt-2 text-sm text-slate-600">Start building a cited study workspace.</p>
        {error ? <p className="mt-5 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
        <label className="mt-6 block text-sm font-medium text-study-navy">
          Name
          <input className="mt-2 w-full rounded border border-study-line px-3 py-2 outline-none focus:border-study-navy" value={name} onChange={(event) => setName(event.target.value)} required />
        </label>
        <label className="mt-4 block text-sm font-medium text-study-navy">
          Email
          <input className="mt-2 w-full rounded border border-study-line px-3 py-2 outline-none focus:border-study-navy" value={email} onChange={(event) => setEmail(event.target.value)} type="email" required />
        </label>
        <label className="mt-4 block text-sm font-medium text-study-navy">
          Password
          <input className="mt-2 w-full rounded border border-study-line px-3 py-2 outline-none focus:border-study-navy" value={password} onChange={(event) => setPassword(event.target.value)} type="password" minLength={8} required />
        </label>
        <button disabled={loading} className="mt-6 w-full rounded bg-study-navy px-4 py-2.5 text-sm font-semibold text-white hover:bg-black disabled:opacity-60">
          {loading ? "Creating..." : "Create account"}
        </button>
        <p className="mt-5 text-center text-sm text-slate-600">
          Already registered? <Link href="/auth/login" className="font-semibold text-study-navy">Log in</Link>
        </p>
      </form>
    </main>
  );
}
