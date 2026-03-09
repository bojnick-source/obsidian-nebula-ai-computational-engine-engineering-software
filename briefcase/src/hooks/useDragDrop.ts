import { useState, useCallback, DragEvent } from "react";
import { useVaultStore } from "../store/useVaultStore";

export function useDragDrop() {
  const [isDragging, setIsDragging] = useState(false);
  const { ingestFiles } = useVaultStore((s) => s.actions);

  const onDragEnter = useCallback((e: DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const onDragOver = useCallback((e: DragEvent) => {
    e.preventDefault();
  }, []);

  const onDragLeave = useCallback((e: DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const onDrop = useCallback(
    async (e: DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const files = Array.from(e.dataTransfer.files);
      if (files.length === 0) return;
      // In Tauri, DataTransfer files have a path property (non-standard)
      const paths = files
        .map((f) => (f as unknown as { path?: string }).path ?? "")
        .filter(Boolean);
      if (paths.length > 0) {
        await ingestFiles(paths);
      }
    },
    [ingestFiles]
  );

  return { isDragging, onDragEnter, onDragOver, onDragLeave, onDrop };
}
