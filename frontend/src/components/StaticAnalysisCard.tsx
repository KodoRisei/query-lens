import type { StaticAnalysis } from "@/types/review";
import SeverityBadge from "./SeverityBadge";

function CountPill({
  count,
  label,
  color,
}: {
  count: number;
  label: string;
  color: string;
}) {
  if (count === 0) return null;
  return (
    <div className={`flex items-center gap-1.5 text-sm ${color}`}>
      <span className="font-semibold tabular-nums">{count}</span>
      <span className="text-slate-400">{label}</span>
    </div>
  );
}

export default function StaticAnalysisCard({
  analysis,
}: {
  analysis: StaticAnalysis;
}) {
  const hasFindings = analysis.findings.length > 0;
  const totalIssues =
    analysis.critical_count + analysis.warning_count + analysis.info_count;

  return (
    <section>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
          Static Analysis
        </h2>
        <div className="flex items-center gap-4">
          <CountPill
            count={analysis.critical_count}
            label="critical"
            color="text-red-400"
          />
          <CountPill
            count={analysis.warning_count}
            label="warning"
            color="text-amber-400"
          />
          <CountPill
            count={analysis.info_count}
            label="info"
            color="text-blue-400"
          />
          {totalIssues === 0 && (
            <span className="text-emerald-400 text-sm font-medium">
              No issues
            </span>
          )}
        </div>
      </div>

      <div className="rounded-lg border border-slate-700 bg-slate-800/50">
        <div className="flex items-center gap-6 px-4 py-3 border-b border-slate-700 text-xs text-slate-400">
          <span>
            Type:{" "}
            <span className="text-slate-200 font-mono">
              {analysis.query_type || "—"}
            </span>
          </span>
          {analysis.table_references.length > 0 && (
            <span>
              Tables:{" "}
              <span className="text-slate-200 font-mono">
                {analysis.table_references.join(", ")}
              </span>
            </span>
          )}
        </div>

        {hasFindings ? (
          <ul className="divide-y divide-slate-700/50">
            {analysis.findings.map((finding, i) => (
              <li key={i} className="px-4 py-3">
                <div className="flex items-start gap-3">
                  <SeverityBadge severity={finding.severity} />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-slate-200">
                      {finding.title}
                    </p>
                    <p className="text-xs text-slate-400 mt-0.5">
                      {finding.message}
                    </p>
                    {finding.suggestion && (
                      <p className="text-xs text-indigo-400 mt-1">
                        {finding.suggestion}
                      </p>
                    )}
                  </div>
                  <span className="text-xs text-slate-600 font-mono shrink-0">
                    {finding.rule_id}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <div className="px-4 py-6 text-center text-sm text-slate-500">
            No static analysis findings.
          </div>
        )}
      </div>
    </section>
  );
}
