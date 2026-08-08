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
    workspaceApi
      .list()
      .then((list) => {
        setWorkspaces(list);
        if (list.length > 0) setCurrent(list[0]);
      })
      .catch(() => setError("Failed to load workspaces"));
  }, []);

  useEffect(() => {
    if (!current) {
      setDocs([]); // eslint-disable-line react-hooks/set-state-in-effect -- reset stale docs on workspace change
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
    <main className="paper flex h-dvh overflow-hidden text-foreground">
      <aside className="flex w-80 flex-col overflow-y-auto border-r-[3px] border-line bg-slag p-4">
        <Link
          href="/"
          className="mb-4 inline-block self-start border-[3px] border-line bg-signal px-3 py-1 font-mono text-xl font-black tracking-tight text-background shadow-[5px_5px_0_0_var(--line)]"
          data-testid="home-link"
        >
          Source<span className="text-ember">IQ</span>
        </Link>

        <div className="border-[3px] border-line bg-panel p-3 shadow-[5px_5px_0_0_var(--line)]">
          <p className="caption mb-2">workspace index</p>
          <form onSubmit={createWorkspace} className="flex flex-col gap-2">
            <input
              data-testid="workspace-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="new/workspace"
              className="focus-ring w-full border-[3px] border-line bg-background px-2.5 py-2 font-mono text-xs font-bold placeholder:text-dim focus:border-signal"
            />
            <button
              data-testid="create-workspace"
              type="submit"
              className="focus-ring border-[3px] border-line bg-foreground px-2.5 py-2 font-mono text-xs font-black text-background shadow-[4px_4px_0_0_var(--line)] transition-transform hover:translate-x-0.5 hover:translate-y-0.5 hover:shadow-[2px_2px_0_0_var(--line)]"
            >
              + SPIN UP
            </button>
          </form>
        </div>

        <ul className="mt-3 flex flex-col gap-2">
          {workspaces.map((w) => (
            <li key={w.id} className="flex items-stretch gap-2">
              <button
                data-testid={`workspace-${w.name}`}
                onClick={() => setCurrent(w)}
                className={`focus-ring flex-1 border-[3px] border-line px-3 py-2 text-left font-mono text-sm font-bold transition-transform ${
                  current?.id === w.id
                    ? "bg-ember text-background shadow-[4px_4px_0_0_var(--line)]"
                    : "bg-panel text-ghost hover:shadow-[4px_4px_0_0_var(--line)]"
                }`}
              >
                {w.name}
              </button>
              <button
                data-testid={`delete-workspace-${w.name}`}
                onClick={() => deleteWorkspace(w.id)}
                className="focus-ring shrink-0 border-[3px] border-line bg-panel px-2 font-bold text-ghost shadow-[3px_3px_0_0_var(--line)] hover:bg-ember hover:text-background"
                aria-label={`Delete workspace ${w.name}`}
              >
                ✕
              </button>
            </li>
          ))}
        </ul>

        {current && (
          <div className="mt-6">
            <h3 className="caption mb-2">attached documents</h3>
            {docs.length === 0 ? (
              <p className="font-mono text-xs font-bold text-dim">[ none attached ]</p>
            ) : (
              <ul className="flex flex-col gap-2">
                {docs.map((d) => (
                  <li key={d.id} className="border-[3px] border-line bg-panel px-3 py-2 shadow-[3px_3px_0_0_var(--line)]">
                    <div className="flex items-center justify-between gap-2">
                      <span className="truncate font-mono text-xs font-bold text-ghost" title={d.name}>
                        {d.name}
                      </span>
                      <button
                        data-testid={`delete-doc-${d.name}`}
                        onClick={() => deleteDoc(d.id)}
                        className="shrink-0 px-1 font-mono text-xs font-bold text-dim hover:text-ember"
                        aria-label={`Delete ${d.name}`}
                      >
                        ✕
                      </button>
                    </div>
                    <span
                      data-testid={`doc-status-${d.name}`}
                      className={[
                        "mt-1 inline-block border-2 border-line px-1.5 py-0.5 font-mono text-[10px] font-black uppercase tracking-widest",
                        d.status === "completed"
                          ? "bg-voltage text-background"
                          : d.status === "failed"
                          ? "bg-ember text-background"
                          : "bg-paper text-ghost",
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
          <div className="flex flex-1 flex-col items-center justify-center gap-3 p-6">
            <span className="border-[3px] border-line bg-signal px-6 py-3 font-mono text-5xl font-black text-background shadow-[8px_8px_0_0_var(--line)]">
              []
            </span>
            <p className="caption mt-3">no channel bound</p>
            <p className="max-w-sm text-center text-sm font-bold text-dim">
              Create a workspace in the left index, then attach documents and open a query
              session.
            </p>
          </div>
        ) : (
          <>
            <header className="flex flex-wrap items-center justify-between gap-3 border-b-[3px] border-line bg-panel px-4 py-3">
              <div className="flex items-center gap-3">
                <h1
                  data-testid="current-workspace"
                  className="font-mono text-xl font-black tracking-tight"
                >
                  {current.name}
                </h1>
                <span className="inline-block border-2 border-line bg-voltage px-2 py-0.5 font-mono text-[10px] font-black uppercase text-background">
                  session live
                </span>
              </div>
              <div className="flex flex-wrap items-center gap-2 font-mono text-xs font-bold">
                <button
                  data-testid="delete-chat"
                  onClick={deleteChat}
                  className="focus-ring border-[3px] border-line bg-background px-2.5 py-1.5 text-ghost shadow-[3px_3px_0_0_var(--line)] hover:translate-x-0.5 hover:translate-y-0.5 hover:shadow-[1px_1px_0_0_var(--line)]"
                >
                  clear chat
                </button>
                <label className="focus-ring inline-block cursor-pointer border-[3px] border-line bg-voltage px-2.5 py-1.5 text-background shadow-[3px_3px_0_0_var(--line)] hover:translate-x-0.5 hover:translate-y-0.5 hover:shadow-[1px_1px_0_0_var(--line)]">
                  {uploading ? "← INGESTING…" : "+ ATTACH FILE"}
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
                  className="focus-ring border-[3px] border-line bg-ember px-2.5 py-1.5 text-background shadow-[3px_3px_0_0_var(--line)] hover:translate-x-0.5 hover:translate-y-0.5 hover:shadow-[1px_1px_0_0_var(--line)]"
                >
                  logout
                </button>
              </div>
            </header>

            <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto p-4">
              {messages.map((m, i) => (
                <div
                  key={i}
                  className={`flex max-w-[82%] flex-col gap-2 border-[3px] border-line p-3 font-mono text-sm ${
                    m.role === "user"
                      ? "self-end bg-ember text-background shadow-[5px_5px_0_0_var(--line)]"
                      : "self-start bg-panel text-ghost shadow-[5px_5px_0_0_var(--line)]"
                  }`}
                >
                  <span className="caption">{m.role === "user" ? "you ▸" : "grid ▸"}</span>
                  <span className="whitespace-pre-wrap">{m.content}</span>
                  {m.role === "assistant" && m.sources && m.sources.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {m.sources.map((s, j) => (
                        <button
                          key={j}
                          data-testid={`source-chip-${s.document}`}
                          onClick={() => showPreview(s)}
                          className="focus-ring cursor-pointer border-[3px] border-line bg-foreground px-2 py-0.5 text-[11px] font-black text-ember shadow-[3px_3px_0_0_var(--line)] hover:translate-x-0.5 hover:translate-y-0.5 hover:shadow-[1px_1px_0_0_var(--line)]"
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
              {busy && (
                <div className="self-start border-[3px] border-line bg-signal p-3 font-mono text-sm font-bold text-background shadow-[5px_5px_0_0_var(--line)]">
                  <span className="animate-pulse">▮▮▮</span> querying index…
                </div>
              )}
            </div>

            <form
              onSubmit={ask}
              className="flex gap-2 border-t-[3px] border-line bg-panel p-3"
            >
              <input
                data-testid="chat-input"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="ask the pile…"
                className="focus-ring min-w-0 flex-1 border-[3px] border-line bg-background px-3 py-2.5 font-mono text-sm font-bold placeholder:text-dim focus:border-signal"
              />
              <button
                data-testid="send"
                type="submit"
                className="focus-ring border-[3px] border-line bg-ember px-6 font-mono text-sm font-black text-background shadow-[5px_5px_0_0_var(--line)] transition-transform hover:translate-x-0.5 hover:translate-y-0.5 hover:shadow-[2px_2px_0_0_var(--line)]"
              >
                RUN
              </button>
            </form>
          </>
        )}
      </section>

      {error && (
        <div className="fixed right-4 bottom-4 z-50 max-w-sm border-[3px] border-line bg-ember p-3 font-mono text-xs font-bold text-background shadow-[5px_5px_0_0_var(--line)]">
          ! {error}
        </div>
      )}

      {preview && (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-foreground/70 p-4">
          <div className="flex max-h-[85vh] w-full max-w-3xl flex-col border-[3px] border-line bg-panel shadow-[10px_10px_0_0_var(--line)]">
            <div className="flex items-center justify-between gap-3 border-b-[3px] border-line px-4 py-3">
              <h3 data-testid="preview-title" className="flex items-center gap-3 font-mono text-sm font-black">
                <span className="inline-block border-2 border-line bg-signal px-1.5 text-background">▶</span>
                {preview.name}
                {preview.page != null && (
                  <span className="border-[3px] border-line bg-ember px-2 py-0.5 font-mono text-[11px] font-black text-background">
                    page {preview.page}
                  </span>
                )}
              </h3>
              <button
                data-testid="preview-close"
                onClick={() => setPreview(null)}
                className="focus-ring border-[3px] border-line bg-background px-2 py-0.5 font-mono text-xs font-bold text-ghost shadow-[3px_3px_0_0_var(--line)] hover:bg-ember hover:text-background"
              >
                ✕ close
              </button>
            </div>
            <div className="flex min-h-0 flex-1 flex-col gap-2 overflow-y-auto px-4 py-3">
              {previewBusy ? (
                <div className="font-mono text-sm font-bold text-ghost">loading byte stream…</div>
              ) : preview.fileUrl && preview.name.match(/\.(png|jpe?g|gif|bmp|tiff?|webp)$/i) ? (
                <img
                  data-testid="preview-image"
                  src={preview.fileUrl}
                  alt={preview.name}
                  className="max-h-[55vh] w-auto self-center border-[3px] border-line bg-slag shadow-[5px_5px_0_0_var(--line)]"
                />
              ) : preview.fileUrl && preview.name.match(/\.pdf$/i) ? (
                <iframe
                  data-testid="preview-pdf"
                  src={`${preview.fileUrl}${preview.page ? `#page=${preview.page}` : ""}`}
                  className="h-[58vh] w-full border-[3px] border-line bg-background shadow-[5px_5px_0_0_var(--line)]"
                  title={preview.name}
                />
              ) : null}
              <div
                data-testid="preview-content"
                className="border-[3px] border-line bg-slag p-3 font-mono text-[13px] whitespace-pre-wrap text-ghost shadow-[4px_4px_0_0_var(--line)]"
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