import clsx from "clsx";
import type { Severity } from "@/types/review";

const STYLES: Record<Severity, string> = {
  critical: "bg-red-500/15 text-red-400 ring-1 ring-red-500/30",
  warning: "bg-amber-500/15 text-amber-400 ring-1 ring-amber-500/30",
  info: "bg-blue-500/15 text-blue-400 ring-1 ring-blue-500/30",
};

const DOTS: Record<Severity, string> = {
  critical: "bg-red-400",
  warning: "bg-amber-400",
  info: "bg-blue-400",
};

export default function SeverityBadge({ severity }: { severity: Severity }) {
  return (
    <span
      className={clsx(
        "inline-flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs font-medium",
        STYLES[severity],
      )}
    >
      <span className={clsx("w-1.5 h-1.5 rounded-full", DOTS[severity])} />
      {severity}
    </span>
  );
}
