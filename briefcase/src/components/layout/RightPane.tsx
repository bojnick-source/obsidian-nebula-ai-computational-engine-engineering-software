import { motion, AnimatePresence } from "framer-motion";
import { useVaultStore } from "../../store/useVaultStore";
import { useUIStore } from "../../store/useUIStore";
import { MetadataPanel } from "../common/MetadataPanel";

export function RightPane() {
  const selectedId = useVaultStore((s) => s.selectedId);
  const assets = useVaultStore((s) => s.assets);
  const rightPaneVisible = useUIStore((s) => s.rightPaneVisible);

  const asset = selectedId ? assets[selectedId] : null;

  return (
    <AnimatePresence initial={false}>
      {rightPaneVisible && (
        <motion.div
          className="shrink-0 flex flex-col overflow-hidden"
          style={{
            width: 300,
            borderLeft: "1px solid rgba(255,255,255,0.06)",
          }}
          initial={{ width: 0, opacity: 0 }}
          animate={{ width: 300, opacity: 1 }}
          exit={{ width: 0, opacity: 0 }}
          transition={{ duration: 0.2, ease: "easeOut" }}
        >
          <MetadataPanel asset={asset} />
        </motion.div>
      )}
    </AnimatePresence>
  );
}
