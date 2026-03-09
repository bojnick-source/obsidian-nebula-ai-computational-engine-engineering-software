import type { Importance } from "../../types/asset";

interface Props {
  importance: Importance;
  size?: "sm" | "md";
}

const IMPORTANCE_CONFIG: Record<
  Importance,
  { label: string; color: string; bg: string }
> = {
  critical: {
    label: "Critical",
    color: "#ef4444",
    bg: "rgba(239,68,68,0.12)",
  },
  executive: {
    label: "Executive",
    color: "#f59e0b",
    bg: "rgba(245,158,11,0.12)",
  },
  technical: {
    label: "Technical",
    color: "#3b82f6",
    bg: "rgba(59,130,246,0.12)",
  },
  research: {
    label: "Research",
    color: "#a855f7",
    bg: "rgba(168,85,247,0.12)",
  },
  approved: {
    label: "Approved",
    color: "#22c55e",
    bg: "rgba(34,197,94,0.12)",
  },
  archived: {
    label: "Archived",
    color: "#6b7280",
    bg: "rgba(107,114,128,0.1)",
  },
};

export function ImportanceChip({ importance, size = "sm" }: Props) {
  const config = IMPORTANCE_CONFIG[importance];
  const isSmall = size === "sm";

  return (
    <span
      style={{
        color: config.color,
        background: config.bg,
        border: `1px solid ${config.color}30`,
      }}
      className={`inline-flex items-center rounded font-medium tracking-wide ${
        isSmall ? "text-[10px] px-1.5 py-0.5" : "text-xs px-2 py-1"
      }`}
    >
      {config.label}
    </span>
  );
}

export function importanceColor(importance: Importance): string {
  return IMPORTANCE_CONFIG[importance].color;
}
