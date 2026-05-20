import type { AiReview } from "@/types/review";

const SEVERITY_COLOR: Record<string, string> = {
  critical: "text-red-400 bg-red-500/10 border-red-500/30",
  warning: "text-amber-400 bg-amber-500/10 border-amber-500/30",
  info: "text-sky-400 bg-sky-500/10 border-sky-500/30",
};

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-2">
      {children}
    </p>
  );
}

export default function AiReviewCard({ review }: { review: AiReview }) {
  return (
    <section>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
          AI Review
        </h2>
        <span className="text-xs text-slate-500">
          {review.provider} / {review.model}
          &nbsp;&middot;&nbsp;
          {review.input_tokens.toLocaleString()} in /{" "}
          {review.output_tokens.toLocaleString()} out tokens
        </span>
      </div>

      <div className="space-y-5">
        {/* ── Summary ─────────────────────────────────────── */}
        <div>
          <SectionLabel>Summary</SectionLabel>
          <div className="rounded-lg border border-slate-700 bg-slate-800/50 px-4 py-3">
            <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">
              {review.summary}
            </p>
          </div>
        </div>

        {/* ── Findings ────────────────────────────────────── */}
        {review.findings.length > 0 && (
          <div>
            <SectionLabel>Findings ({review.findings.length})</SectionLabel>
            <div className="space-y-2">
              {review.findings.map((finding, i) => (
                <div
                  key={i}
                  className="rounded-lg border border-slate-700 bg-slate-800/50 px-4 py-3 space-y-1.5"
                >
                  {/* rule_id badge */}
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-400">
                      #{i + 1}
                    </span>
                    <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-slate-700 text-slate-300">
                      {finding.rule_id}
                    </span>
                  </div>

                  {/* explanation */}
                  <p className="text-sm text-slate-200 leading-relaxed">
                    {finding.explanation}
                  </p>

                  {/* suggestion */}
                  {finding.suggestion && (
                    <div className="flex gap-2 pt-0.5">
                      <span className="mt-0.5 shrink-0 text-indigo-400">→</span>
                      <p className="text-sm text-indigo-300 leading-relaxed">
                        {finding.suggestion}
                      </p>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* ── Improved Query ───────────────────────────────── */}
        {review.improved_query && (
          <div>
            <SectionLabel>Improved Query</SectionLabel>
            <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5 overflow-hidden">
              <div className="flex items-center gap-2 px-4 py-2 border-b border-emerald-500/20 bg-emerald-500/5">
                <div className="w-2 h-2 rounded-full bg-emerald-400" />
                <span className="text-xs font-medium text-emerald-400">
                  Suggested Rewrite
                </span>
              </div>
              <pre className="px-4 py-3 text-xs font-mono text-slate-200 overflow-x-auto whitespace-pre-wrap leading-relaxed">
                {review.improved_query}
              </pre>
            </div>
          </div>
        )}

        {/* ── Educational Note ─────────────────────────────── */}
        {review.educational_note && (
          <div>
            <SectionLabel>Educational Note</SectionLabel>
            <div className="rounded-lg border border-blue-500/20 bg-blue-500/5 px-4 py-3">
              <p className="text-sm text-slate-300 leading-relaxed whitespace-pre-wrap">
                {review.educational_note}
              </p>
            </div>
          </div>
        )}
      </div>
    </section>
  );
}
