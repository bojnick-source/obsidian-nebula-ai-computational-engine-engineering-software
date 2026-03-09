import { motion, AnimatePresence } from "framer-motion";
import type { DrawerGroup as DrawerGroupType } from "../../types/asset";
import { useVaultStore } from "../../store/useVaultStore";
import { FileCard } from "./FileCard";
import { importanceColor } from "./ImportanceChip";

interface Props {
  group: DrawerGroupType;
}

export function DrawerGroup({ group }: Props) {
  const assets = useVaultStore((s) => s.assets);
  const { toggleDrawer } = useVaultStore((s) => s.actions);

  const accentColor = group.importance
    ? importanceColor(group.importance)
    : "rgba(255,255,255,0.2)";

  const groupAssets = group.assetIds
    .map((id) => assets[id])
    .filter(Boolean);

  return (
    <div
      className="rounded-xl overflow-hidden"
      style={{ border: "1px solid rgba(255,255,255,0.06)" }}
    >
      {/* Drawer header */}
      <button
        onClick={() => toggleDrawer(group.key)}
        className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-white/[0.04] transition-colors"
        style={{
          background: "rgba(255,255,255,0.02)",
          borderLeft: `3px solid ${accentColor}`,
        }}
      >
        <motion.span
          className="text-white/40 text-xs"
          animate={{ rotate: group.isOpen ? 90 : 0 }}
          transition={{ duration: 0.15 }}
        >
          ▶
        </motion.span>
        <span className="flex-1 text-white/70 text-sm font-medium">
          {group.label}
        </span>
        <span
          className="text-[11px] font-mono px-2 py-0.5 rounded"
          style={{
            color: "rgba(255,255,255,0.3)",
            background: "rgba(255,255,255,0.06)",
          }}
        >
          {groupAssets.length}
        </span>
      </button>

      {/* Drawer content */}
      <AnimatePresence initial={false}>
        {group.isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            style={{ overflow: "hidden" }}
          >
            <div className="p-3 grid gap-2" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))" }}>
              {groupAssets.map((asset) => (
                <FileCard key={asset.id} asset={asset} />
              ))}
              {groupAssets.length === 0 && (
                <p className="col-span-full text-white/20 text-xs py-4 text-center">
                  No files
                </p>
              )}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
