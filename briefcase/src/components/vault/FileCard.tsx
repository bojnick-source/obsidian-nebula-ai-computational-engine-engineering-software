import type { AssetRecord } from "../../types/asset";
import { ImportanceChip } from "./ImportanceChip";
import { useUIStore } from "../../store/useUIStore";
import { useVaultStore } from "../../store/useVaultStore";

interface Props {
  asset: AssetRecord;
}

function mimeIcon(fileType: string): string {
  if (fileType.startsWith("image/")) return "🖼";
  if (fileType.startsWith("video/")) return "🎬";
  if (fileType.startsWith("audio/")) return "🎵";
  if (fileType === "application/pdf") return "📕";
  if (fileType.includes("word")) return "📝";
  if (fileType.includes("spreadsheet") || fileType.includes("excel")) return "📊";
  if (fileType.includes("presentation") || fileType.includes("powerpoint")) return "📊";
  if (fileType.startsWith("model/") || ["glb", "gltf", "stl", "obj"].some((e) => fileType.includes(e))) return "🧊";
  if (fileType.startsWith("text/")) return "📄";
  return "📎";
}

export function FileCard({ asset }: Props) {
  const { openPreview } = useUIStore((s) => s.actions);
  const { selectAsset } = useVaultStore((s) => s.actions);
  const selectedId = useVaultStore((s) => s.selectedId);

  const isSelected = selectedId === asset.id;
  const isArchived = asset.importance === "archived";

  const handleClick = () => {
    selectAsset(asset.id);
  };

  const handleDoubleClick = () => {
    openPreview(asset.id);
  };

  return (
    <div
      onClick={handleClick}
      onDoubleClick={handleDoubleClick}
      className={`group relative flex flex-col cursor-pointer rounded-xl transition-all duration-150 p-3 gap-2 select-none ${
        isArchived ? "opacity-40 grayscale" : ""
      } ${
        isSelected
          ? "bg-white/10 ring-1 ring-white/20"
          : "bg-white/[0.03] hover:bg-white/[0.07]"
      }`}
      style={{
        border: "1px solid rgba(255,255,255,0.06)",
      }}
      title={`${asset.title}\n${asset.originalName}\n\nDouble-click to preview`}
    >
      {/* Thumbnail area */}
      <div
        className="w-full rounded-lg overflow-hidden flex items-center justify-center bg-graphite-800"
        style={{ height: "80px" }}
      >
        <span className="text-3xl opacity-60">{mimeIcon(asset.fileType)}</span>
      </div>

      {/* Title */}
      <p className="text-white/80 text-xs font-medium leading-tight line-clamp-2 min-h-[2rem]">
        {asset.title}
      </p>

      {/* Footer chips */}
      <div className="flex items-center gap-1.5 flex-wrap">
        <ImportanceChip importance={asset.importance} />
        <span className="text-white/20 text-[10px] font-mono">
          {asset.fileType.split("/")[1]?.slice(0, 6).toUpperCase() ?? "FILE"}
        </span>
      </div>

      {/* Hover preview button */}
      <button
        onClick={(e) => {
          e.stopPropagation();
          openPreview(asset.id);
        }}
        className="absolute top-2 right-2 w-6 h-6 rounded-md bg-graphite-600/80 text-white/50 hover:text-white/90 items-center justify-center text-xs opacity-0 group-hover:opacity-100 transition-opacity hidden md:flex"
        title="Preview"
      >
        ⊞
      </button>
    </div>
  );
}
