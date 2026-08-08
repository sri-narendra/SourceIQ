"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

import {
  chatApi,
  documentApi,
  workspaceApi,
} from "@/services/api-endpoints";
import type { IChatSource } from "@/types";

interface Workspace {
  id: string;
  name: string;
  description?: string | null;
}

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  sources?: IChatSource[];
}

interface Doc {
  id: string;
  name: string;
  status: string;
  uploaded_at?: string;
}

export default function DashboardPage() {
  const router = useRouter();
  const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
  const [current, setCurrent] = useState<Workspace | null>(null);
  const [name, setName] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [docs, setDocs] = useState<Doc[]>([]);
  const [uploading, setUploading] = useState(false);
  const [preview, setPreview] = useState<{
    name: string;
    content: string;
    page?: number | null;
    fileUrl?: string;
  } | null>(null);
  const [previewBusy, setPreviewBusy] = useState(false);

  useEffect(() => {
    if (!preview) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setPreview(null);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [preview]);

  useEffect(() => {
    loadWorkspaces();
  }, []);

  async function loadWorkspaces() {
    try {
      const list = await workspaceApi.list();
      setWorkspaces(list);
      if (list.length > 0) setCurrent(list[0]);
    } catch {
      setError("Failed to load workspaces");
    }
  }

  useEffect(() => {
    if (!current) {
      setDocs([]);
      return;
    }
    documentApi
      .list(current.id)
      .then(setDocs)
      .catch(() => setDocs([]));
  }, [current]);

  useEffect(() => {
    if (!current || docs.every((d) => d.status !== "processing")) return;
    const t = setInterval(() => {
      documentApi
        .list(current.id)
        .then(setDocs)
        .catch(() => {});
    }, 3000);
    return () => clearInterval(t);
  }, [current, docs]);

  async function createWorkspace(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    const res = (await workspaceApi.create(name.trim())).data as {
      workspace_id: string;
    };
    const created: Workspace = {
      id: res.workspace_id,
      name: name.trim(),
    };
    setName("");
    setWorkspaces((w) => [...w, created]);
    setCurrent(created);
  }

  async function uploadDoc(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? []);
    if (files.length === 0 || !current) return;
    e.target.value = "";
    setError(null);
    setUploading(true);
    const results: string[] = [];
    for (const file of files) {
      try {
        await documentApi.upload(current.id, file);
        results.push(`${file.name}: uploaded`);
      } catch (err: unknown) {
        const detail = (err as { response?: { data?: { detail?: string } } })
          ?.response?.data?.detail;
        results.push(`${file.name}: ${detail ?? "Error"}`);
      }
    }
    setUploading(false);
    if (results.some((r) => r.endsWith("Error") || r.endsWith("failed"))) {
      setError(results.join(" | "));
    }
    documentApi
      .list(current.id)
      .then(setDocs)
      .catch(() => setDocs([]));
  }

  async function deleteDoc(id: string) {
    try {
      await documentApi.remove(id);
      setDocs((ds) => ds.filter((d) => d.id !== id));
      setError(null);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail;
      setError(detail ?? "Delete failed");
    }
  }

  async function deleteWorkspace(id: string) {
    try {
      await workspaceApi.remove(id);
      const remaining = workspaces.filter((w) => w.id !== id);
      setWorkspaces(remaining);
      if (current?.id === id) {
        setCurrent(remaining[0] ?? null);
        setDocs([]);
        setMessages([]);
        setConversationId(null);
      }
      setError(null);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail;
      setError(detail ?? "Delete failed");
    }
  }

  async function deleteChat() {
    if (conversationId) {
      try {
        await chatApi.remove(conversationId);
      } catch {
        // ignore — clear the UI either way
      }
    }
    setMessages([]);
    setConversationId(null);
  }

  function logout() {
    localStorage.removeItem("token");
    router.push("/login");
  }

  async function showPreview(s: IChatSource) {
    if (!s.document_id) return;
    setPreviewBusy(true);
    try {
      const [p, url] = await Promise.all([
        documentApi.preview(s.document_id),
        documentApi.fileUrl(s.document_id),
      ]);
      setPreview({
        name: p.name,
        content: s.content ?? p.content,
        page: s.page,
        fileUrl: url,
      });
    } catch {
      setPreview({
        name: s.document,
        content: s.content ?? "(preview unavailable)",
        page: s.page,
      });
    } finally {
      setPreviewBusy(false);
    }
  }

  async function ask(e: React.FormEvent) {
    e.preventDefault();
    if (!input.trim() || !current || busy) return;
    const question = input.trim();
    setInput("");
    setMessages((m) => [...m, { role: "user", content: question }]);
    setBusy(true);
    try {
      const body: {
        workspace_id: string;
        message: string;
        conversation_id?: string;
      } = {
        workspace_id: current.id,
        message: question,
      };
      if (conversationId) body.conversation_id = conversationId;
      const res = await chatApi.ask(body);
      if (res.conversation_id) setConversationId(res.conversation_id);
      setMessages((m) => [
        ...m,
        { role: "assistant", content: res.answer, sources: res.sources },
      ]);
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })
        ?.response?.data?.detail;
      setMessages((m) => [
        ...m,
        { role: "assistant", content: detail ?? "Error" },
      ]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="flex h-dvh overflow-hidden bg-zinc-50 dark:bg-black">
      <aside className="w-72 border-r border-zinc-200 p-4 dark:border-zinc-800">
        <Link
          href="/"
          className="mb-4 block font-mono text-lg font-semibold text-zinc-900 hover:text-emerald-600 dark:text-zinc-50 dark:hover:text-emerald-400"
          data-testid="home-link"
        >
          Source<span className="text-emerald-500">IQ</span>
        </Link>
        <h2 className="mb-4 text-lg font-semibold">Workspaces</h2>
        <form onSubmit={createWorkspace} className="mb-4 flex flex-col gap-2">
          <input
            data-testid="workspace-name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="New workspace name"
            className="rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-900"
          />
          <button
            data-testid="create-workspace"
            type="submit"
            className="rounded-lg bg-zinc-900 px-3 py-2 text-white dark:bg-zinc-50 dark:text-black"
          >
            Create
          </button>
        </form>
        <ul className="flex flex-col gap-1">
          {workspaces.map((w) => (
            <li key={w.id} className="flex items-center gap-1">
              <button
                data-testid={`workspace-${w.name}`}
                onClick={() => setCurrent(w)}
                className={`flex-1 rounded-lg px-3 py-2 text-left text-sm ${
                  current?.id === w.id
                    ? "bg-zinc-900 text-white dark:bg-zinc-50 dark:text-black"
                    : "hover:bg-zinc-200 dark:hover:bg-zinc-900"
                }`}
              >
                {w.name}
              </button>
              <button
                data-testid={`delete-workspace-${w.name}`}
                onClick={() => deleteWorkspace(w.id)}
                className="shrink-0 rounded-lg px-2 py-2 text-zinc-400 hover:text-red-600"
                aria-label={`Delete workspace ${w.name}`}
              >
                ✕
              </button>
            </li>
          ))}
        </ul>
        {current && (
          <div className="mt-6">
            <h3 className="mb-2 text-sm font-semibold text-zinc-500">Documents</h3>
            {docs.length === 0 ? (
              <p className="text-xs text-zinc-400">No documents yet</p>
            ) : (
              <ul className="flex flex-col gap-1">
                {docs.map((d) => (
                  <li
                    key={d.id}
                    className="rounded-lg border border-zinc-200 px-3 py-2 text-xs dark:border-zinc-800"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <span className="truncate font-medium" title={d.name}>
                        {d.name}
                      </span>
                      <button
                        data-testid={`delete-doc-${d.name}`}
                        onClick={() => deleteDoc(d.id)}
                        className="shrink-0 text-zinc-400 hover:text-red-600"
                        aria-label={`Delete ${d.name}`}
                      >
                        ✕
                      </button>
                    </div>
                    <span
                      data-testid={`doc-status-${d.name}`}
                      className={[
                        d.status === "completed"
                          ? "text-green-600 dark:text-green-400"
                          : d.status === "failed"
                          ? "text-red-600 dark:text-red-400"
                          : "text-amber-600 dark:text-amber-400",
                      ].join(" ")}
                    >
                      {d.status}
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </aside>

      <section className="flex min-h-0 flex-1 flex-col">
        {!current ? (
          <div className="flex flex-1 items-center justify-center text-zinc-500">
            Create a workspace to get started
          </div>
        ) : (
          <>
            <header className="flex items-center justify-between border-b border-zinc-200 p-4 dark:border-zinc-800">
              <h1 data-testid="current-workspace" className="text-xl font-semibold">
                {current.name}
              </h1>
              <button
                data-testid="delete-chat"
                onClick={deleteChat}
                className="cursor-pointer text-sm text-zinc-500 underline hover:text-zinc-700 dark:hover:text-zinc-300"
              >
                Delete chat
              </button>
              <label className="cursor-pointer text-sm text-zinc-500 underline">
                {uploading ? "Uploading…" : "Upload document"}
                <input
                  data-testid="upload-doc"
                  type="file"
                  multiple
                  accept=".pdf,.docx,.pptx,.xlsx,.odt,.txt,.md,.csv,.tsv,.json,.xml,.html,.yaml,.yml,.rtf,.py,.js,.ts,.java,.cpp,.go,.rs,.rb,.php,.swift,.kt,.sh,.log,.png,.jpg,.jpeg,.bmp,.tif,.tiff,.webp"
                  className="hidden"
                  onChange={uploadDoc}
                />
              </label>
              <button
                data-testid="logout"
                onClick={logout}
                className="rounded-lg border border-zinc-300 px-3 py-1 text-sm text-zinc-600 hover:bg-zinc-100 dark:border-zinc-700 dark:text-zinc-300 dark:hover:bg-zinc-800"
              >
                Log out
              </button>
            </header>

            <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto p-4">
              {messages.map((m, i) => (
                <div
                  key={i}
                  className={`flex max-w-[80%] flex-col gap-2 rounded-lg px-4 py-2 text-sm ${
                    m.role === "user"
                      ? "self-end bg-zinc-900 text-white dark:bg-zinc-50 dark:text-black"
                      : "self-start bg-white dark:bg-zinc-900"
                  }`}
                >
                  <span className="whitespace-pre-wrap">{m.content}</span>
                  {m.role === "assistant" && m.sources && m.sources.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {m.sources.map((s, j) => (
                        <button
                          key={j}
                          data-testid={`source-chip-${s.document}`}
                          onClick={() => showPreview(s)}
                          className={`rounded-full px-2 py-0.5 text-[11px] bg-zinc-100 text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300 hover:bg-zinc-200 hover:text-zinc-800 dark:hover:bg-zinc-700 dark:hover:text-zinc-100 cursor-pointer`}
                        >
                          {s.document}
                          {s.page != null && ` · p${s.page}`}
                          {typeof s.score === "number" && ` · ${(s.score * 100).toFixed(0)}%`}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}
              {busy && <div className="text-sm text-zinc-500">Thinking…</div>}
            </div>

            <form onSubmit={ask} className="flex gap-2 border-t border-zinc-200 p-4 dark:border-zinc-800">
              <input
                data-testid="chat-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask a question about your documents"
                className="flex-1 rounded-lg border border-zinc-300 px-3 py-2 dark:border-zinc-700 dark:bg-zinc-900"
              />
              <button
                data-testid="send"
                type="submit"
                className="rounded-lg bg-zinc-900 px-4 py-2 text-white dark:bg-zinc-50 dark:text-black"
              >
                Send
              </button>
            </form>
          </>
        )}
      </section>
      {error && <p className="text-sm text-red-600">{error}</p>}
      {preview && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
          <div className="flex max-h-[80vh] w-full max-w-2xl flex-col rounded-xl bg-white dark:bg-zinc-900 shadow-xl">
            <div className="flex items-center justify-between border-b border-zinc-200 px-4 py-3 dark:border-zinc-800">
              <h3 data-testid="preview-title" className="text-sm font-semibold">
                {preview.name}
                {preview.page != null && (
                  <span className="ml-2 rounded-full bg-zinc-100 px-2 py-0.5 text-[11px] font-normal text-zinc-600 dark:bg-zinc-800 dark:text-zinc-300">
                    Page {preview.page}
                  </span>
                )}
              </h3>
              <button
                data-testid="preview-close"
                onClick={() => setPreview(null)}
                className="rounded-md px-2 py-0.5 text-zinc-500 hover:bg-zinc-100 dark:hover:bg-zinc-800"
              >
                Esc / ✕
              </button>
            </div>
            <div className="flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto px-4 py-3 text-sm text-zinc-700 dark:text-zinc-300">
              {previewBusy ? (
                "Loading preview…"
              ) : preview.fileUrl && preview.name.match(/\.(png|jpe?g|gif|bmp|tiff?|webp)$/i) ? (
                <img
                  data-testid="preview-image"
                  src={preview.fileUrl}
                  alt={preview.name}
                  className="max-h-[60vh] w-auto self-center rounded-lg border border-zinc-200 dark:border-zinc-800"
                />
              ) : preview.fileUrl && preview.name.match(/\.pdf$/i) ? (
                <iframe
                  data-testid="preview-pdf"
                  src={`${preview.fileUrl}${preview.page ? `#page=${preview.page}` : ""}`}
                  className="h-[60vh] w-full rounded-lg border border-zinc-200 dark:border-zinc-800"
                  title={preview.name}
                />
              ) : null}
              <div
                data-testid="preview-content"
                className="whitespace-pre-wrap rounded-lg bg-zinc-50 p-3 dark:bg-zinc-800/50"
              >
                {preview.content}
              </div>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
