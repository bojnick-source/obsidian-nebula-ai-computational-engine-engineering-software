import type { AssetRecord } from "../../types/asset";
import { ImportanceChip } from "../vault/ImportanceChip";
import { useUIStore } from "../../store/useUIStore";

interface Props {
  asset: AssetRecord | null;
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  if (value === null || value === undefined || value === "") return null;
  return (
    <div className="grid grid-cols-[100px,1fr] gap-2 text-xs">
      <span className="text-white/30 pt-0.5 shrink-0">{label}</span>
      <span className="text-white/70 break-words">{value}</span>
    </div>
  );
}

function confidentialityColor(c: string) {
  if (c === "confidential") return "text-red-400";
  if (c === "unrestricted") return "text-green-400";
  return "text-white/50";
}

export function MetadataPanel({ asset }: Props) {
  const { openPreview } = useUIStore((s) => s.actions);

  if (!asset) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3 px-6 text-center">
        <div className="w-10 h-10 rounded-lg bg-graphite-700 flex items-center justify-center opacity-40">
          <span className="text-xl">📋</span>
        </div>
        <p className="text-white/20 text-xs">Select a file to view details</p>
      </div>
    );
  }

  const formattedDate = (iso: string) => {
    try {
      return new Date(iso).toLocaleString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return iso;
    }
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 shrink-0" style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
        <div className="flex items-start gap-2 mb-2">
          <ImportanceChip importance={asset.importance} size="md" />
          <span
            className={`text-xs font-mono ${confidentialityColor(asset.confidentiality)}`}
          >
            {asset.confidentiality.toUpperCase()}
          </span>
        </div>
        <p className="text-white/90 font-medium text-sm leading-snug">{asset.title}</p>
        <p className="text-white/30 text-xs mt-0.5 truncate">{asset.originalName}</p>
      </div>

      {/* Scrollable fields */}
      <div className="flex-1 overflow-y-auto px-4 py-3 flex flex-col gap-2.5">
        <Field label="MIME type" value={asset.fileType} />
        <Field label="Project" value={asset.project} />
        <Field label="Subproject" value={asset.subproject} />
        <Field label="Audience" value={asset.audience} />
        <Field
          label="Vetted"
          value={
            <span
              className={
                asset.vettedStatus === "final-locked"
                  ? "text-green-400"
                  : asset.vettedStatus === "unvetted"
                  ? "text-orange-400"
                  : "text-white/70"
              }
            >
              {asset.vettedStatus}
            </span>
          }
        />
        <Field label="Version" value={`v${asset.version}`} />
        <Field label="Source agent" value={asset.sourceAgent} />
        <Field label="Pipeline ID" value={asset.pipelineId} />
        <Field label="Ingested" value={formattedDate(asset.ingestedAt)} />
        <Field label="Created" value={formattedDate(asset.createdAt)} />

        {asset.tags.length > 0 && (
          <div className="grid grid-cols-[100px,1fr] gap-2 text-xs">
            <span className="text-white/30 pt-1 shrink-0">Tags</span>
            <div className="flex flex-wrap gap-1">
              {asset.tags.map((tag) => (
                <span
                  key={tag}
                  className="px-1.5 py-0.5 rounded text-[10px]"
                  style={{
                    background: "rgba(255,255,255,0.07)",
                    color: "rgba(255,255,255,0.55)",
                  }}
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        )}

        {asset.classificationExplanation && (
          <div className="mt-2">
            <p className="text-white/20 text-[10px] uppercase tracking-wider mb-1">
              Classification
            </p>
            <p className="text-white/40 text-xs leading-relaxed">
              {asset.classificationExplanation}
            </p>
            {asset.classificationConfidence > 0 && (
              <div className="mt-1.5 flex items-center gap-2">
                <div
                  className="h-1 rounded-full flex-1"
                  style={{ background: "rgba(255,255,255,0.08)" }}
                >
                  <div
                    className="h-1 rounded-full"
                    style={{
                      width: `${asset.classificationConfidence * 100}%`,
                      background:
                        asset.classificationConfidence >= 0.7
                          ? "#22c55e"
                          : "#f59e0b",
                    }}
                  />
                </div>
                <span className="text-white/30 text-[10px] tabular-nums">
                  {Math.round(asset.classificationConfidence * 100)}%
                </span>
              </div>
            )}
          </div>
        )}

        <Field
          label="Content hash"
          value={
            <span className="font-mono text-[9px] text-white/20 break-all">
              {asset.contentHash.slice(0, 16)}…
            </span>
          }
        />
      </div>

      {/* Actions footer */}
      <div
        className="px-4 py-3 shrink-0 flex gap-2"
        style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}
      >
        <button
          onClick={() => openPreview(asset.id)}
          className="flex-1 py-2 rounded-lg text-xs font-medium transition-colors text-blue-400 hover:text-blue-300"
          style={{ background: "rgba(59,130,246,0.1)", border: "1px solid rgba(59,130,246,0.2)" }}
        >
          Preview
        </button>
      </div>
    </div>
  );
}
