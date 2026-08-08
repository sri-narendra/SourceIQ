import Link from "next/link";

const FORMATS = [
  "PDF", "PNG", "DOCX", "XLSX", "PPTX", "MD", "TXT",
  "CSV", "JSON", "TIF", "PY", "RTF",
] as const;

const SPEC = [
  ["01", "INGEST", "40+ formats. Every byte routed: text decode, office unzip, or OCR pass."],
  ["02", "CHUNK", "Page-aware splits. A PDF page is a unit of truth; answers carry the p-number."],
  ["03", "EMBED", "Vector index built on every chunk. No headless scanning at query time."],
  ["04", "CITE", "Every answer pins its source: file, page, score. Verify or discard."],
] as const;

const TICKER =
  "LOAD EVERYTHING  +  ANSWER WITH THE PAGE NUMBER  +  CLICK A CITATION TO READ THE ORIGINAL  +  ";

export default function Home() {
  return (
    <div className="paper min-h-dvh text-foreground selection:bg-signal selection:text-background">
      <header className="sticky top-0 z-40 border-b-[3px] border-line bg-paper/90">
        <div className="mx-auto grid max-w-7xl grid-cols-[1fr_auto] items-center gap-6 px-6 py-4">
          <Link href="/" className="inline-block border-[3px] border-line bg-signal px-3 py-1 font-mono text-xl font-black tracking-tight text-background shadow-[5px_5px_0_0_var(--line)]">
            Source<span className="text-ember">IQ</span><span className="ml-2 text-sm font-bold no-underline">file-brain</span>
          </Link>
          <nav className="flex items-center gap-3 font-mono text-xs font-bold uppercase tracking-widest text-ghost">
            <a href="#io" className="border-[3px] border-transparent px-1 hover:border-line">load</a>
            <a href="#proc" className="border-[3px] border-transparent px-1 hover:border-line">grind</a>
            <Link href="/login" className="border-[3px] border-line bg-foreground px-3 py-1.5 text-background shadow-[4px_4px_0_0_var(--line)] hover:translate-y-0.5 hover:shadow-[2px_2px_0_0_var(--line)]">
              go →
            </Link>
          </nav>
        </div>
      </header>

      <div className="ticker border-y-[3px] border-line bg-foreground py-2 text-background" aria-hidden="true">
        <div className="tape font-mono text-xs font-bold uppercase tracking-widest">
          <span className="px-2">{TICKER}</span>
          <span className="px-2">{TICKER}</span>
          <span className="px-2">{TICKER}</span>
          <span className="px-2">{TICKER}</span>
        </div>
      </div>

      <main className="mx-auto max-w-7xl px-6">
        <section id="io" className="grid gap-10 py-16 md:grid-cols-[1.15fr_0.85fr] md:py-24">
          <div>
            <p className="caption mb-5 inline-block whitespace-nowrap rounded-full border-2 border-line bg-panel px-3 py-1">
              You upload it. We dissect it.
            </p>
            <h1 className="text-5xl leading-[0.9] font-black tracking-tight md:text-7xl">
              Load every file.
              <br />
              <span className="text-signal">Point answers</span>
              <span className="text-ember"> at the page.</span>
              <br />
              Prove or discard.
            </h1>
            <p className="mt-6 max-w-xl text-lg leading-relaxed text-ghost md:text-xl">
              PDFs, spreadsheets, slides, code, scans. Drop whatever you have, SourceIQ chops it into
              page-indexed chunks, and answers any question, with the source file and page number
              taped to the reply.
            </p>
            <div className="mt-8 flex flex-wrap gap-3">
              <Link href="/login" className="border-[3px] border-line bg-ember px-6 py-3.5 text-base font-black text-background shadow-[6px_6px_0_0_var(--line)] transition-transform hover:translate-x-0.5 hover:translate-y-0.5 hover:shadow-[3px_3px_0_0_var(--line)]">
                LOAD A DOCUMENT →
              </Link>
              <a href="#proc" className="border-[3px] border-line bg-panel px-6 py-3.5 text-base font-black text-ghost shadow-[6px_6px_0_0_var(--line)] transition-transform hover:translate-x-0.5 hover:translate-y-0.5 hover:shadow-[3px_3px_0_0_var(--line)]">
                HOW THE GRIND WORKS
              </a>
            </div>
            <dl className="mt-12 grid grid-cols-3 gap-3">
              {[
                ["FORMATS", `${FORMATS.length}+`],
                ["CHUNK SIZE", "800 tok"],
                ["PAGE TAG", "YES"],
              ].map(([k, v], i) => (
                <div key={k} className={"border-[3px] border-line p-4 shadow-[5px_5px_0_0_var(--line)] " + (i === 1 ? "bg-voltage" : i === 2 ? "bg-panel" : "bg-signal")}>
                  <dt className="caption text-background/90">{k}</dt>
                  <dd className="mt-1 text-2xl font-black text-foreground">{v}</dd>
                </div>
              ))}
            </dl>
          </div>

          <div className="self-start border-[3px] border-line bg-panel p-5 shadow-[9px_9px_0_0_var(--line)] md:mt-8">
            <div className="mb-4 flex items-center justify-between border-b-[3px] border-dashed border-line pb-3">
              <span className="font-mono text-xs font-black uppercase tracking-widest text-ghost">live query · t+0:12:07</span>
              <span className="inline-block border-2 border-line bg-ember px-2 py-0.5 font-mono text-[10px] font-black uppercase text-background">
                real log
              </span>
            </div>
            <pre className="mb-4 overflow-x-auto font-mono text-[13px] leading-relaxed whitespace-pre-wrap text-ghost">
{`> what drives the coaxial feed?
< page 4 of service_manual.pdf:
  feed is a 9-pin stepper, 24 V, 1.8°/step.
» source taped: service_manual.pdf p4 · 0.82`}
            </pre>
            <div className="flex flex-wrap gap-2">
              <span className="border-[3px] border-line bg-foreground px-2 py-1 font-mono text-[11px] font-bold text-ember">
                ▤ service_manual.pdf p4 · 0.82
              </span>
              <span className="border-2 border-line bg-signal px-2 py-1 font-mono text-[11px] font-bold text-background">
                heatmap.png · ocr · 0.71
              </span>
              <span className="border-2 border-line bg-voltage px-2 py-1 font-mono text-[11px] font-bold text-background">
                click to open original
              </span>
            </div>
            <div className="mt-6 grid grid-cols-2 gap-3">
              <div className="border-[3px] border-line bg-slag p-3">
                <p className="caption mb-2">retrieval</p>
                <div className="flex items-end gap-1" style={{ height: 48 }}>
                  {[34, 50, 68, 55, 82].map((h, i) => (
                    <span key={i} style={{ height: `${h}%` }} className="flex-1 bg-signal" />
                  ))}
                </div>
              </div>
              <div className="border-[3px] border-line bg-slag p-3">
                <p className="caption mb-2">status</p>
                <ul className="font-mono text-[11px] font-bold text-ghost">
                  <li className="flex justify-between py-0.5"><span>pages</span><span className="ml-2 text-ember">42</span></li>
                  <li className="flex justify-between py-0.5"><span>chunks</span><span className="ml-2 text-ember">137</span></li>
                  <li className="flex justify-between py-0.5"><span>index</span><span className="ml-2 text-ember">seeded</span></li>
                </ul>
              </div>
            </div>
          </div>
        </section>

        <section id="proc" className="pt-4 pb-16 md:pb-24">
          <p className="caption mb-8">
            <span className="mr-2 inline-block border-2 border-line bg-ember px-2 py-0.5 text-background">▲</span>
            the grind, in four steps
          </p>
          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {SPEC.map(([n, t, d], i) => (
              <div key={n} className={"border-[3px] border-line p-5 shadow-[6px_6px_0_0_var(--line)] " + (i % 2 ? "bg-panel" : "bg-foreground")}>
                <div className="mb-3 inline-block border-[3px] border-line bg-background px-2 py-1 font-mono text-sm font-black shadow-[3px_3px_0_0_var(--line)]">
                  {n}
                </div>
                <h3 className="mb-2 font-mono text-xl font-black tracking-tight text-foreground">{t}</h3>
                <p className="text-sm leading-relaxed text-ghost">{d}</p>
              </div>
            ))}
          </div>

          <div className="mt-14">
            <p className="caption mb-4">admitted data types</p>
            <div className="flex flex-wrap gap-2.5">
              {FORMATS.map((f) => (
                <span key={f} className="border-2 border-line bg-panel px-3 py-1 font-mono text-sm font-black text-ghost shadow-[3px_3px_0_0_var(--line)]">
                  {f}
                </span>
              ))}
            </div>
          </div>
        </section>

        <section className="border-y-[3px] border-line bg-ember py-16 text-center md:py-20">
          <p className="mb-3 font-mono text-xs font-black uppercase tracking-widest text-background">
            ready to interrogate your documents?
          </p>
          <h2 className="mx-auto max-w-3xl text-4xl leading-tight font-black tracking-tight text-background md:text-5xl">
            Answers taped to the source page are answers you can.
            <br className="hidden md:block" />
            check.
          </h2>
          <div className="mt-8 flex justify-center">
            <Link href="/login" className="inline-block border-[3px] border-line bg-background px-8 py-4 text-lg font-black text-ember shadow-[6px_6px_0_0_var(--line)] transition-transform hover:translate-x-0.5 hover:translate-y-0.5 hover:shadow-[3px_3px_0_0_var(--line)]">
              SPIN UP →
            </Link>
          </div>
        </section>
      </main>

      <footer className="border-t-[3px] border-line">
        <div className="mx-auto flex max-w-7xl flex-wrap items-center justify-between gap-3 px-6 py-5 font-mono text-xs font-bold text-ghost">
          <span>Source<span className="text-ember">IQ</span> — every file becomes a page-verified answer.</span>
          <span className="hidden sm:inline">api: fastapi · vec: pgvector · ocr: rapid</span>
        </div>
      </footer>
    </div>
  );
}