import ReviewWorkspace from "@/components/ReviewWorkspace";

export default function Home() {
  return (
    <div className="flex flex-col min-h-screen">
      <header className="border-b border-slate-800 px-6 py-4 flex items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded bg-indigo-500 flex items-center justify-center">
            <svg
              width="16"
              height="16"
              viewBox="0 0 16 16"
              fill="none"
              aria-hidden="true"
            >
              <path
                d="M2 4h12M2 8h8M2 12h5"
                stroke="white"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
              <circle cx="13" cy="11" r="2.5" stroke="white" strokeWidth="1.5" />
              <path
                d="M14.8 12.8L16 14"
                stroke="white"
                strokeWidth="1.5"
                strokeLinecap="round"
              />
            </svg>
          </div>
          <span className="font-semibold text-slate-100 tracking-tight">
            QueryLens
          </span>
        </div>
        <span className="text-slate-500 text-sm">AI-powered SQL review</span>
      </header>
      <main className="flex-1 p-6">
        <ReviewWorkspace />
      </main>
      <footer className="border-t border-slate-800 px-6 py-3 text-center text-slate-600 text-xs">
        Deterministic analysis first — AI augments, never replaces.
      </footer>
    </div>
  );
}
