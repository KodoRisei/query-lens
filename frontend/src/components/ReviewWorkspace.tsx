"use client";

import dynamic from "next/dynamic";
import { useState, useEffect } from "react";
import clsx from "clsx";
import { createReview, ApiError } from "@/lib/api";
import type { QueryReview, ReviewMode, Language } from "@/types/review";
import StaticAnalysisCard from "./StaticAnalysisCard";
import AiReviewCard from "./AiReviewCard";
import ExecutionPlanCard from "./ExecutionPlanCard";

const SqlEditor = dynamic(() => import("./SqlEditor"), {
  ssr: false,
  loading: () => (
    <div className="h-44 rounded-lg border border-slate-700 bg-slate-800/50 animate-pulse" />
  ),
});

const MODES: { value: ReviewMode; label: string; description: string }[] = [
  {
    value: "junior",
    label: "Junior",
    description: "Plain-language explanations, educational focus",
  },
  {
    value: "senior",
    label: "Senior",
    description: "Concise, direct feedback for experienced engineers",
  },
  {
    value: "performance",
    label: "Performance",
    description: "Deep dive into query costs and bottlenecks",
  },
];

const LOADING_STEPS = [
  "Running static analysis…",
  "Running EXPLAIN ANALYZE…",
  "Asking AI…",
];

const PLACEHOLDER_SQL = `-- game1 スキーマのサンプルクエリ（そのままReviewできます）
SELECT *
FROM game1.user_m u, game1.login_log l
WHERE u.user_id = l.user_id
  AND u.country_code LIKE '%JP%'
ORDER BY l.create_time DESC`;

export default function ReviewWorkspace() {
  const [sql, setSql] = useState(PLACEHOLDER_SQL);
  const [reviewMode, setReviewMode] = useState<ReviewMode>("senior");
  const [language, setLanguage] = useState<Language>("en");
  const [loading, setLoading] = useState(false);
  const [loadingStep, setLoadingStep] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [review, setReview] = useState<QueryReview | null>(null);

  useEffect(() => {
    if (!loading) { setLoadingStep(0); return; }
    // Rough timing: static(<1s) → EXPLAIN(<5s) → AI(5s+)
    const t1 = setTimeout(() => setLoadingStep(1), 800);
    const t2 = setTimeout(() => setLoadingStep(2), 5500);
    return () => { clearTimeout(t1); clearTimeout(t2); };
  }, [loading]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!sql.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await createReview({ sql: sql.trim(), review_mode: reviewMode, language });
      setReview(result);
    } catch (err) {
      if (err instanceof ApiError) {
        setError(`${err.code}: ${err.message}`);
      } else {
        setError("Unexpected error — is the backend running?");
      }
    } finally {
      setLoading(false);
    }
  }

  const totalIssues = review
    ? review.static_analysis.critical_count +
      review.static_analysis.warning_count +
      review.static_analysis.info_count +
      (review.execution_plan?.findings.length ?? 0)
    : null;

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Editor panel */}
      <form onSubmit={handleSubmit} className="space-y-3">
        <SqlEditor value={sql} onChange={setSql} disabled={loading} />

        <div className="flex flex-wrap items-center gap-3">
          {/* Review mode selector */}
          <div className="flex items-center gap-1 p-1 rounded-lg bg-slate-800 border border-slate-700">
            {MODES.map((mode) => (
              <button
                key={mode.value}
                type="button"
                onClick={() => setReviewMode(mode.value)}
                title={mode.description}
                className={clsx(
                  "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                  reviewMode === mode.value
                    ? "bg-indigo-600 text-white"
                    : "text-slate-400 hover:text-slate-200",
                )}
              >
                {mode.label}
              </button>
            ))}
          </div>

          {/* Language toggle */}
          <div className="flex items-center gap-1 p-1 rounded-lg bg-slate-800 border border-slate-700">
            {(["en", "ja"] as Language[]).map((lang) => (
              <button
                key={lang}
                type="button"
                onClick={() => setLanguage(lang)}
                className={clsx(
                  "px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
                  language === lang
                    ? "bg-slate-600 text-white"
                    : "text-slate-400 hover:text-slate-200",
                )}
              >
                {lang === "en" ? "EN" : "日本語"}
              </button>
            ))}
          </div>

          <button
            type="submit"
            disabled={loading || !sql.trim()}
            className={clsx(
              "px-5 py-2 rounded-lg text-sm font-semibold transition-all",
              loading || !sql.trim()
                ? "bg-slate-700 text-slate-500 cursor-not-allowed"
                : "bg-indigo-600 hover:bg-indigo-500 text-white shadow-lg shadow-indigo-500/20",
            )}
          >
            {loading ? (
              <span className="flex items-center gap-2">
                <svg className="animate-spin w-4 h-4" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                {LOADING_STEPS[loadingStep]}
              </span>
            ) : (
              "Review Query"
            )}
          </button>

          {review && (
            <span className="text-xs text-slate-500 ml-auto">
              ID: <span className="font-mono">{review.id.slice(0, 8)}…</span>
              {" · "}
              {new Date(review.created_at).toLocaleTimeString()}
            </span>
          )}
        </div>
      </form>

      {/* Error state */}
      {error && (
        <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-400">
          {error}
        </div>
      )}

      {/* Results */}
      {review && (
        <div className="space-y-4">
          {/* Summary bar */}
          <div className="flex items-center gap-3 px-4 py-3 rounded-lg bg-slate-800/50 border border-slate-700">
            <div
              className={clsx(
                "w-2.5 h-2.5 rounded-full",
                totalIssues === 0
                  ? "bg-emerald-400"
                  : review.static_analysis.critical_count > 0
                    ? "bg-red-400"
                    : "bg-amber-400",
              )}
            />
            <span className="text-sm text-slate-300">
              {totalIssues === 0
                ? "No issues found"
                : `${totalIssues} issue${totalIssues === 1 ? "" : "s"} found`}
            </span>
            <span className="text-xs text-slate-500 ml-auto capitalize">
              {review.review_mode} mode
            </span>
          </div>

          <StaticAnalysisCard analysis={review.static_analysis} />
          <AiReviewCard review={review.ai_review} />
          {review.execution_plan && (
            <ExecutionPlanCard plan={review.execution_plan} />
          )}
        </div>
      )}

      {/* Empty state */}
      {!review && !loading && !error && (
        <div className="flex flex-col items-center gap-3 py-16 text-center">
          <div className="w-12 h-12 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center">
            <svg
              width="22"
              height="22"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              className="text-slate-500"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3.75 9.776c.112-.017.227-.026.344-.026h15.812c.117 0 .232.009.344.026m-16.5 0a2.25 2.25 0 00-1.883 2.542l.857 6a2.25 2.25 0 002.227 1.932H19.05a2.25 2.25 0 002.227-1.932l.857-6a2.25 2.25 0 00-1.883-2.542m-16.5 0V6A2.25 2.25 0 016 3.75h3.879a1.5 1.5 0 011.06.44l2.122 2.12a1.5 1.5 0 001.06.44H18A2.25 2.25 0 0120.25 9v.776"
              />
            </svg>
          </div>
          <p className="text-sm text-slate-500">
            Paste a SQL query above and click{" "}
            <span className="text-slate-400">Review Query</span> to begin.
          </p>
        </div>
      )}
    </div>
  );
}
