import { useVaultStore } from "../../store/useVaultStore";
import { importanceColor } from "../vault/ImportanceChip";
import type { Importance } from "../../types/asset";

const IMPORTANCE_ORDER: Importance[] = [
  "critical",
  "executive",
  "technical",
  "research",
  "approved",
  "archived",
];

export function LeftRail() {
  const assets = useVaultStore((s) => s.assets);
  const groupBy = useVaultStore((s) => s.groupBy);
  const showArchived = useVaultStore((s) => s.showArchived);
  const { setGroupBy, toggleShowArchived } = useVaultStore((s) => s.actions);

  const allAssets = Object.values(assets);

  // Project list
  const projects = [...new Set(allAssets.map((a) => a.project).filter(Boolean))];

  // Importance counts
  const importanceCounts = IMPORTANCE_ORDER.reduce<Record<string, number>>(
    (acc, imp) => {
      acc[imp] = allAssets.filter((a) => a.importance === imp).length;
      return acc;
    },
    {}
  );

  type GroupOption = typeof groupBy;
  const groupOptions: { value: GroupOption; label: string }[] = [
    { value: "project", label: "Project" },
    { value: "fileType", label: "File Type" },
    { value: "importance", label: "Priority" },
    { value: "recency", label: "Recency" },
  ];

  return (
    <div
      className="flex flex-col h-full overflow-hidden"
      style={{ borderRight: "1px solid rgba(255,255,255,0.06)" }}
    >
      {/* App title */}
      <div className="px-4 pt-4 pb-3 shrink-0">
        <div className="flex items-center gap-2">
          <span className="text-lg">💼</span>
          <span className="text-white/90 font-semibold text-sm tracking-wide">
            Briefcase
          </span>
        </div>
        <p className="text-white/20 text-[10px] mt-0.5 tracking-widest uppercase">
          Executive Output Repository
        </p>
      </div>

      <div className="flex-1 overflow-y-auto px-3 pb-4 flex flex-col gap-5">
        {/* Group by selector */}
        <section>
          <p className="text-white/20 text-[10px] uppercase tracking-widest mb-2 px-1">
            Group By
          </p>
          <div className="flex flex-col gap-0.5">
            {groupOptions.map((opt) => (
              <button
                key={opt.value}
                onClick={() => setGroupBy(opt.value)}
                className={`flex items-center px-3 py-2 rounded-lg text-xs transition-colors ${
                  groupBy === opt.value
                    ? "text-white/90 bg-white/10"
                    : "text-white/40 hover:text-white/70 hover:bg-white/[0.04]"
                }`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </section>

        {/* Priority overview */}
        <section>
          <p className="text-white/20 text-[10px] uppercase tracking-widest mb-2 px-1">
            Priority
          </p>
          <div className="flex flex-col gap-0.5">
            {IMPORTANCE_ORDER.filter((imp) => importanceCounts[imp] > 0).map(
              (imp) => (
                <button
                  key={imp}
                  onClick={() => setGroupBy("importance")}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs text-white/40 hover:text-white/70 hover:bg-white/[0.04] transition-colors"
                >
                  <span
                    className="w-1.5 h-1.5 rounded-full shrink-0"
                    style={{ background: importanceColor(imp) }}
                  />
                  <span className="flex-1 capitalize">{imp}</span>
                  <span className="text-white/20 tabular-nums">
                    {importanceCounts[imp]}
                  </span>
                </button>
              )
            )}
          </div>
        </section>

        {/* Projects */}
        {projects.length > 0 && (
          <section>
            <p className="text-white/20 text-[10px] uppercase tracking-widest mb-2 px-1">
              Projects
            </p>
            <div className="flex flex-col gap-0.5">
              {projects.map((project) => (
                <button
                  key={project}
                  className="flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs text-white/40 hover:text-white/70 hover:bg-white/[0.04] transition-colors"
                >
                  <span className="text-white/20">📁</span>
                  <span className="flex-1 truncate">{project}</span>
                </button>
              ))}
            </div>
          </section>
        )}

        {/* Archive toggle */}
        <section className="mt-auto">
          <button
            onClick={toggleShowArchived}
            className={`w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs transition-colors ${
              showArchived
                ? "text-white/60 bg-white/[0.07]"
                : "text-white/30 hover:text-white/50 hover:bg-white/[0.04]"
            }`}
          >
            <span>🗄</span>
            <span>Show Archived</span>
            {showArchived && (
              <span className="ml-auto text-white/30">✓</span>
            )}
          </button>
        </section>
      </div>
    </div>
  );
}
