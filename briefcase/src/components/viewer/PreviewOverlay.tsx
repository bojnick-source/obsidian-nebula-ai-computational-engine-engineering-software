import { useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useUIStore } from "../../store/useUIStore";
import { useVaultStore } from "../../store/useVaultStore";
import { ViewerPluginHost } from "./ViewerPluginHost";
import { ImportanceChip } from "../vault/ImportanceChip";

export function PreviewOverlay() {
  const { previewOpen, previewAssetId, actions } = useUIStore((s) => ({
    previewOpen: s.previewOpen,
    previewAssetId: s.previewAssetId,
    actions: s.actions,
  }));
  const assets = useVaultStore((s) => s.assets);

  const asset = previewAssetId ? assets[previewAssetId] : null;

  // Close on Escape key
  useEffect(() => {
    if (!previewOpen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape") actions.closePreview();
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [previewOpen, actions]);

  return (
    <AnimatePresence>
      {previewOpen && asset && (
        <>
          {/* Backdrop */}
          <motion.div
            className="fixed inset-0 z-40 bg-black/80 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            onClick={actions.closePreview}
          />

          {/* Preview panel */}
          <motion.div
            className="fixed inset-4 z-50 rounded-2xl overflow-hidden flex flex-col"
            style={{
              background: "rgba(15, 15, 15, 0.97)",
              border: "1px solid rgba(255,255,255,0.08)",
              boxShadow: "0 24px 80px rgba(0,0,0,0.8)",
            }}
            initial={{ opacity: 0, scale: 0.97 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.97 }}
            transition={{ duration: 0.15, ease: "easeOut" }}
          >
            {/* Header */}
            <div
              className="flex items-center gap-3 px-5 py-3 shrink-0"
              style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}
            >
              <ImportanceChip importance={asset.importance} />
              <div className="flex-1 min-w-0">
                <p className="text-white/90 font-medium truncate text-sm">
                  {asset.title}
                </p>
                <p className="text-white/30 text-xs truncate">
                  {asset.originalName}
                </p>
              </div>
              <span className="text-white/20 text-xs font-mono px-2 py-0.5 rounded bg-graphite-700">
                {asset.fileType.split("/")[1]?.toUpperCase() ?? "FILE"}
              </span>
              <button
                onClick={actions.closePreview}
                className="ml-2 w-8 h-8 rounded-lg flex items-center justify-center text-white/40 hover:text-white/80 hover:bg-graphite-700 transition-colors"
              >
                ✕
              </button>
            </div>

            {/* Content */}
            <div className="flex-1 min-h-0 overflow-hidden">
              <ViewerPluginHost asset={asset} />
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
