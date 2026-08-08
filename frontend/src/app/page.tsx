import Link from "next/link";

export default function Home() {
  return (
    <div className="min-h-dvh bg-zinc-950 text-zinc-100">
      <header className="sticky top-0 z-10 border-b border-zinc-800/80 bg-zinc-950/80 backdrop-blur">
        <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
          <span className="font-mono text-sm tracking-tight text-zinc-100">
            Source<span className="text-emerald-400">IQ</span>
          </span>
          <div className="flex items-center gap-6 text-sm text-zinc-400">
            <a href="#features" className="hover:text-zinc-100">Features</a>
            <a href="#how" className="hover:text-zinc-100">How it works</a>
            <Link
              href="/login"
              className="rounded-lg border border-zinc-700 px-3 py-1.5 hover:border-zinc-500 hover:text-zinc-100"
            >
              Sign in
            </Link>
          </div>
        </nav>
      </header>

      <main className="mx-auto max-w-6xl px-6">
        <section className="grid gap-10 py-24 md:grid-cols-[1.2fr_1fr] md:py-36">
          <div>
            <p className="mb-6 font-mono text-xs tracking-widest text-emerald-400 uppercase">
              Upload anything. PDF → PNG.
            </p>
            <h1 className="text-4xl leading-tight font-semibold tracking-tight md:text-6xl">
              Ask over any document,
              <br />
              <span className="text-zinc-500">answered with its source.</span>
            </h1>
            <p className="mt-6 max-w-lg text-lg text-zinc-400">
              Drop in PDFs, Word, Excel, slides, code, even scanned pages and images.
              Chat with the corpus — every answer cites the file and the exact page
              it came from, with a one-click preview.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link
                href="/login"
                className="rounded-lg bg-emerald-400 px-5 py-2.5 text-sm font-medium text-zinc-950 hover:bg-emerald-300"
              >
                Try it free
              </Link>
              <a
                href="#how"
                className="rounded-lg border border-zinc-700 px-5 py-2.5 text-sm text-zinc-300 hover:border-zinc-500"
              >
                See how it works
              </a>
            </div>
          </div>

          <div className="self-center rounded-2xl border border-zinc-800 bg-zinc-900/60 p-5 shadow-2xl shadow-black/40">
            <div className="mb-4 flex items-center gap-2 border-b border-zinc-800 pb-3">
              <span className="font-mono text-xs text-zinc-400">Q</span>
              <span className="text-sm">What kind of chart is shown on page 4 of the report?</span>
            </div>
            <div className="mb-4 rounded-lg bg-zinc-800/60 p-4 text-sm text-zinc-300">
              Page 4 shows a quarterly revenue bar chart... 
              <span className="mt-2 block font-mono text-xs text-zinc-500">…</span>
            </div>
            <div className="flex flex-wrap gap-2">
              <span className="rounded-full border border-emerald-400/40 bg-emerald-400/10 px-2.5 py-1 font-mono text-[11px] text-emerald-300">
                Q3_report.pdf · p4 · 82%
              </span>
              <span className="rounded-full border border-zinc-700 bg-zinc-800/60 px-2.5 py-1 font-mono text-[11px] text-zinc-400">
                chart.png · 74%
              </span>
            </div>
          </div>
        </section>

        <section id="features" className="border-t border-zinc-800/80 py-20">
          <h2 className="mb-12 text-center text-2xl font-semibold md:text-3xl">
            Everything lands in the same chat
          </h2>
          <div className="grid gap-4 md:grid-cols-3">
            {[
              {
                t: "40+ file formats",
                d: "Text, Markdown, code, Office docs, PDFs, and OCR'd images — PNG, JPG, TIFF and more.",
              },
              {
                t: "Page-aware answers",
                d: "Chunks are tagged with their page; every citation reports which page the data came from.",
              },
              {
                t: "Cite-to-verify previews",
                d: "Click a source chip to open the file — PDFs jump straight to the cited page.",
              },
            ].map((f) => (
              <div
                key={f.t}
                className="rounded-2xl border border-zinc-800 bg-zinc-900/40 p-6 hover:border-zinc-700"
              >
                <h3 className="mb-2 font-medium">{f.t}</h3>
                <p className="text-sm text-zinc-400">{f.d}</p>
              </div>
            ))}
          </div>
        </section>

        <section id="how" className="border-t border-zinc-800 py-20">
          <h2 className="mb-12 text-center text-2xl font-semibold md:text-3xl">
            From upload to a cited answer in four steps
          </h2>
          <div className="grid gap-4 md:grid-cols-4">
            {[
              ["1", "Upload", "Any file type for extracted, OCR'd into text."],
              ["2", "Ingest", "Page-aware chunks are embedded into a vector index."],
              ["3", "Ask", "Chat with your documents in natural language."],
              ["4", "Verify", "Click a source chip to preview the exact page cited."],
            ].map(([n, t, d]) => (
              <div key={n} className="rounded-2xl border border-zinc-800 p-5">
                <span className="font-mono text-emerald-400">{n}</span>
                <h3 className="mt-2 font-semibold">{t}</h3>
                <p className="mt-1 text-sm text-zinc-400">{d}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="py-24 text-center">
          <h2 className="mb-6 text-3xl font-semibold md:text-4xl">
            Your documents, finally answerable.
          </h2>
          <Link
            href="/login"
            className="inline-block rounded-lg bg-emerald-400 px-6 py-3 text-sm font-medium text-zinc-950 hover:bg-emerald-300"
          >
            Create a workspace
          </Link>
        </section>
      </main>

      <footer className="border-t border-zinc-800/80 py-8">
        <div className="mx-auto max-w-6xl px-6 font-mono text-xs text-zinc-500">
          Source<span className="text-emerald-400">IQ</span> — local-first RAG. Runs with no
          AWS, no API keys.
        </div>
      </footer>
    </div>
  );
}