"use client";

import { useRouter } from "next/navigation";
import Link from "next/link";
import { useState } from "react";

import { authApi } from "@/services/api-endpoints";
import WarmUp from "@/components/WarmUp";

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
    <main className="paper flex min-h-dvh items-center justify-center p-6 text-foreground">
      <WarmUp />
      <div className="w-full max-w-md">
        <Link href="/" className="inline-block border-[3px] border-line bg-signal px-3 py-1 font-mono text-lg font-black tracking-tight text-background shadow-[5px_5px_0_0_var(--line)]">
          Source<span className="text-ember">IQ</span><span className="ml-2 text-xs font-bold">auth</span>
        </Link>

        <div className="mt-8 border-[3px] border-line bg-panel p-8 shadow-[9px_9px_0_0_var(--line)]">
          <div className="mb-6 flex items-center justify-between gap-3 border-b-[3px] border-dashed border-line pb-4">
            <h1 className="font-mono text-2xl font-black tracking-tight">
              {mode === "login" ? "Who&apos;s there?" : "New identity"}
            </h1>
            <span className="border-2 border-line bg-ember px-2 py-1 font-mono text-[10px] font-black uppercase text-background">
              {mode === "login" ? "sign in" : "register"}
            </span>
          </div>

          <form onSubmit={submit} className="space-y-6">
            {mode === "register" && (
              <label className="block">
                <span className="caption mb-2 block">designation</span>
                <input
                  data-testid="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  required
                  placeholder="Big Boss"
                  className="focus-ring w-full border-[3px] border-line bg-background px-3 py-3 font-mono text-sm font-bold placeholder:text-dim focus:border-signal"
                />
              </label>
            )}

            <label className="block">
              <span className="caption mb-2 block">email</span>
              <input
                data-testid="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="you@station.local"
                className="focus-ring w-full border-[3px] border-line bg-background px-3 py-3 font-mono text-sm font-bold placeholder:text-dim focus:border-signal"
              />
            </label>

            <label className="block">
              <span className="caption mb-2 block">password</span>
              <input
                data-testid="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                placeholder="••••••••"
                className="focus-ring w-full border-[3px] border-line bg-background px-3 py-3 font-mono text-sm font-bold placeholder:text-dim focus:border-signal"
              />
            </label>

            {error && (
              <p className="border-[3px] border-line bg-ember px-3 py-2 font-mono text-xs font-bold text-background shadow-[4px_4px_0_0_var(--line)]">
                ! {error}
              </p>
            )}

            <button
              data-testid="submit"
              type="submit"
              className="focus-ring block w-full border-[3px] border-line bg-foreground px-4 py-3.5 font-mono text-sm font-black uppercase text-background shadow-[6px_6px_0_0_var(--line)] transition-transform hover:translate-x-0.5 hover:translate-y-0.5 hover:shadow-[3px_3px_0_0_var(--line)]"
            >
              {mode === "login" ? "LET ME IN" : "CREATE ACCOUNT"}
            </button>

            <p className="text-center font-mono text-xs font-bold text-dim">
              {mode === "login" ? (
                <>Don&apos;t have one? <button type="button" onClick={() => setMode("register")} className="text-ember underline decoration-2 underline-offset-4 hover:text-ghost">register here</button></>
              ) : (
                <>Already keyed in? <button type="button" onClick={() => setMode("login")} className="text-ember underline decoration-2 underline-offset-4 hover:text-ghost">back to sign in</button></>
              )}
            </p>
          </form>
        </div>
      </div>
    </main>
  );
}