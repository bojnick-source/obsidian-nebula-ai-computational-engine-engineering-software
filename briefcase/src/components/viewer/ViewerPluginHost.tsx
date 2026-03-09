import { useEffect, useRef, useState } from "react";
import type { AssetRecord } from "../../types/asset";
import { resolvePlugin } from "../../hooks/useViewer";
import { getFileUrl } from "../../ipc/commands";

interface Props {
  asset: AssetRecord;
}

export function ViewerPluginHost({ asset }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const plugin = resolvePlugin(asset);
    let disposed = false;

    const run = async () => {
      setLoading(true);
      setError(null);
      try {
        if (!plugin) {
          setLoading(false);
          return;
        }
        const objectUrl = await getFileUrl(asset.contentHash);
        if (disposed) return;
        await plugin.renderPreview(container, asset, objectUrl);
      } catch (err) {
        if (!disposed) setError(String(err));
      } finally {
        if (!disposed) setLoading(false);
      }
    };

    run();

    return () => {
      disposed = true;
      plugin?.dispose();
      if (container) container.innerHTML = "";
    };
  }, [asset]);

  const plugin = resolvePlugin(asset);

  if (!plugin) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-4 text-center px-8">
        <div className="w-16 h-16 rounded-xl bg-graphite-700 flex items-center justify-center">
          <span className="text-2xl">📄</span>
        </div>
        <div>
          <p className="text-white/70 font-medium">{asset.originalName}</p>
          <p className="text-white/30 text-sm mt-1">{asset.fileType}</p>
          <p className="text-white/20 text-xs mt-3">
            No viewer available for this file type
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative h-full w-full">
      {loading && (
        <div className="absolute inset-0 flex items-center justify-center z-10 bg-graphite-900/80">
          <div className="w-8 h-8 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
        </div>
      )}
      {error && (
        <div className="absolute inset-0 flex items-center justify-center z-10 px-8">
          <div className="text-center">
            <p className="text-red-400 text-sm">Failed to render preview</p>
            <p className="text-white/30 text-xs mt-2">{error}</p>
          </div>
        </div>
      )}
      <div ref={containerRef} className="h-full w-full" />
    </div>
  );
}
