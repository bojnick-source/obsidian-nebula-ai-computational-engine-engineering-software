import { AnimatePresence, motion } from "framer-motion";
import { useDragDrop } from "../../hooks/useDragDrop";

export function DropZone({ children }: { children: React.ReactNode }) {
  const { isDragging, onDragEnter, onDragOver, onDragLeave, onDrop } = useDragDrop();

  return (
    <div
      className="relative flex-1 min-h-0"
      onDragEnter={onDragEnter}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
    >
      {children}

      <AnimatePresence>
        {isDragging && (
          <motion.div
            className="absolute inset-0 z-30 flex flex-col items-center justify-center pointer-events-none"
            style={{
              background: "rgba(59,130,246,0.08)",
              border: "2px dashed rgba(59,130,246,0.5)",
              borderRadius: "12px",
              backdropFilter: "blur(4px)",
            }}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.1 }}
          >
            <span className="text-4xl mb-3">📥</span>
            <p className="text-blue-400 font-medium text-sm">
              Drop files to import
            </p>
            <p className="text-white/30 text-xs mt-1">
              Files will be ingested into Briefcase
            </p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
