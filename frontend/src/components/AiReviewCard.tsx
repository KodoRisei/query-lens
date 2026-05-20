"use client";

import { useState } from "react";
import type { AiReview } from "@/types/review";

function SectionLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-xs font-semibold text-slate-500 uppercase tracking-widest mb-2">
      {children}
    </p>
  );
}

function CopyButton({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  async function handleCopy() {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <button
      onClick={handleCopy}
      className="text-xs px-2 py-1 rounded bg-slate-700 hover:bg-slate-600 text-slate-300 transition-colors"
    >
      {copied ? "Copied!" : "Copy"}
    </button>
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
        {/* ── Summary ──────────────────────────────────────── */}
        <div>
          <SectionLabel>Summary</SectionLabel>
          <div className="rounded-lg border border-slate-700 bg-slate-800/50 px-4 py-3">
            <p className="text-sm text-slate-200 leading-relaxed whitespace-pre-wrap">
              {review.summary}
            </p>
          </div>
        </div>

        {/* ── Findings ─────────────────────────────────────── */}
        {review.findings.length > 0 && (
          <div>
            <SectionLabel>Findings ({review.findings.length})</SectionLabel>
            <div className="space-y-2">
              {review.findings.map((finding, i) => (
                <div
                  key={i}
                  className="rounded-lg border border-slate-700 bg-slate-800/50 px-4 py-3 space-y-1.5"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-400">
                      #{i + 1}
                    </span>
                    <span className="text-xs font-mono px-1.5 py-0.5 rounded bg-slate-700 text-slate-300">
                      {finding.rule_id}
                    </span>
                  </div>
                  <p className="text-sm text-slate-200 leading-relaxed">
                    {finding.explanation}
                  </p>
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
              <div className="flex items-center justify-between px-4 py-2 border-b border-emerald-500/20 bg-emerald-500/5">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-emerald-400" />
                  <span className="text-xs font-medium text-emerald-400">
                    Suggested Rewrite
                  </span>
                </div>
                <CopyButton text={review.improved_query} />
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
