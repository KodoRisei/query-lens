import type { AiReview } from "@/types/review";

export default function AiReviewCard({ review }: { review: AiReview }) {
  return (
    <section>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
          AI Review
        </h2>
        <span className="text-xs text-slate-500">
          {review.provider} / {review.model} &middot;{" "}
          {(review.input_tokens + review.output_tokens).toLocaleString()} tokens
        </span>
      </div>

      <div className="space-y-3">
        {/* Summary */}
        <div className="rounded-lg border border-slate-700 bg-slate-800/50 px-4 py-3">
          <p className="text-sm text-slate-200 leading-relaxed">
            {review.summary}
          </p>
        </div>

        {/* AI findings */}
        {review.findings.length > 0 && (
          <div className="rounded-lg border border-slate-700 bg-slate-800/50 divide-y divide-slate-700/50">
            {review.findings.map((finding, i) => (
              <div key={i} className="px-4 py-3">
                <p className="text-xs font-mono text-slate-500 mb-1">
                  {finding.rule_id}
                </p>
                <p className="text-sm text-slate-300">{finding.explanation}</p>
                {finding.suggestion && (
                  <p className="text-xs text-indigo-400 mt-1.5">
                    {finding.suggestion}
                  </p>
                )}
              </div>
            ))}
          </div>
        )}

        {/* Improved query */}
        {review.improved_query && (
          <div className="rounded-lg border border-emerald-500/30 bg-emerald-500/5">
            <div className="flex items-center gap-2 px-4 py-2 border-b border-emerald-500/20">
              <div className="w-2 h-2 rounded-full bg-emerald-400" />
              <span className="text-xs font-medium text-emerald-400">
                Suggested Rewrite
              </span>
            </div>
            <pre className="px-4 py-3 text-xs font-mono text-slate-200 overflow-x-auto whitespace-pre-wrap leading-relaxed">
              {review.improved_query}
            </pre>
          </div>
        )}

        {/* Educational note */}
        {review.educational_note && (
          <div className="rounded-lg border border-blue-500/20 bg-blue-500/5 px-4 py-3">
            <p className="text-xs font-medium text-blue-400 mb-1">
              Educational note
            </p>
            <p className="text-sm text-slate-300 leading-relaxed">
              {review.educational_note}
            </p>
          </div>
        )}
      </div>
    </section>
  );
}
