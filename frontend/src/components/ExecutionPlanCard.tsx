import type { ExecutionPlan } from "@/types/review";
import SeverityBadge from "./SeverityBadge";

function TimingPill({
  label,
  value,
}: {
  label: string;
  value: number | null;
}) {
  if (value === null) return null;
  return (
    <div className="text-xs text-slate-400">
      {label}:{" "}
      <span className="text-slate-200 font-mono tabular-nums">
        {value.toFixed(2)} ms
      </span>
    </div>
  );
}

export default function ExecutionPlanCard({ plan }: { plan: ExecutionPlan }) {
  return (
    <section>
      <div className="flex items-center justify-between mb-3">
        <h2 className="text-sm font-semibold text-slate-300 uppercase tracking-wider">
          Execution Plan
        </h2>
        <div className="flex items-center gap-4">
          {!plan.has_analyze_data && (
            <span className="text-xs text-amber-500">
              EXPLAIN only (no ANALYZE)
            </span>
          )}
          <TimingPill label="Planning" value={plan.planning_time_ms} />
          <TimingPill label="Execution" value={plan.execution_time_ms} />
        </div>
      </div>

      <div className="rounded-lg border border-slate-700 bg-slate-800/50">
        {plan.findings.length > 0 ? (
          <ul className="divide-y divide-slate-700/50">
            {plan.findings.map((finding, i) => (
              <li key={i} className="px-4 py-3">
                <div className="flex items-start gap-3">
                  <SeverityBadge severity={finding.severity} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <p className="text-sm font-medium text-slate-200">
                        {finding.title}
                      </p>
                      {finding.relation_name && (
                        <span className="text-xs font-mono text-slate-500 bg-slate-700/50 px-1.5 py-0.5 rounded">
                          {finding.relation_name}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-slate-400">{finding.message}</p>
                    {finding.suggestion && (
                      <p className="text-xs text-indigo-400 mt-1">
                        {finding.suggestion}
                      </p>
                    )}
                  </div>
                  <span className="text-xs text-slate-600 font-mono shrink-0">
                    {finding.node_type}
                  </span>
                </div>
              </li>
            ))}
          </ul>
        ) : (
          <div className="px-4 py-6 text-center text-sm text-slate-500">
            No bottlenecks detected in execution plan.
          </div>
        )}
      </div>
    </section>
  );
}
