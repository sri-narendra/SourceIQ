"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { authApi } from "@/services/api-endpoints";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      if (mode === "register") {
        await authApi.register(name, email, password);
      }
      await authApi.login(email, password);
      router.push("/dashboard");
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail;
      setError(detail ?? "Something went wrong");
    }
  }

  return (
    <main className="flex flex-1 items-center justify-center bg-zinc-50 p-6 dark:bg-black">
      <form
        onSubmit={submit}
        className="w-full max-w-sm rounded-2xl border border-zinc-200 bg-white p-8 dark:border-zinc-800 dark:bg-zinc-950"
      >
        <p className="mb-1 font-mono text-sm text-zinc-500 dark:text-zinc-400">
          Source<span className="text-emerald-500">IQ</span>
        </p>
        <h1 className="mb-6 text-2xl font-semibold text-zinc-900 dark:text-zinc-50">
          {mode === "login" ? "Sign in" : "Create account"}
        </h1>

        {mode === "register" && (
          <label className="mb-3 block">
            <span className="text-sm text-zinc-600 dark:text-zinc-400">Name</span>
            <input
              data-testid="name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
              className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-900"
            />
          </label>
        )}

        <label className="mb-3 block">
          <span className="text-sm text-zinc-600 dark:text-zinc-400">Email</span>
          <input
            data-testid="email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-900"
          />
        </label>

        <label className="mb-5 block">
          <span className="text-sm text-zinc-600 dark:text-zinc-400">Password</span>
          <input
            data-testid="password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            className="mt-1 w-full rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-900"
          />
        </label>

        {error && <p className="mb-4 text-sm text-red-600">{error}</p>}

        <button
          data-testid="submit"
          type="submit"
          className="w-full rounded-lg bg-zinc-900 px-4 py-2 text-white dark:bg-zinc-50 dark:text-black"
        >
          {mode === "login" ? "Sign in" : "Create account"}
        </button>

        <button
          type="button"
          onClick={() => setMode(mode === "login" ? "register" : "login")}
          className="mt-3 w-full text-center text-sm text-zinc-500 underline"
        >
          {mode === "login" ? "Need an account? Register" : "Have an account? Sign in"}
        </button>
      </form>
    </main>
  );
}
