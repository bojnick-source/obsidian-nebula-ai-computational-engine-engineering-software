import { create } from "zustand";

interface UIState {
  previewOpen: boolean;
  previewAssetId: string | null;
  rightPaneVisible: boolean;
  actions: {
    openPreview: (assetId: string) => void;
    closePreview: () => void;
    toggleRightPane: () => void;
  };
}

export const useUIStore = create<UIState>((set) => ({
  previewOpen: false,
  previewAssetId: null,
  rightPaneVisible: true,

  actions: {
    openPreview: (assetId) =>
      set({ previewOpen: true, previewAssetId: assetId }),
    closePreview: () =>
      set({ previewOpen: false, previewAssetId: null }),
    toggleRightPane: () =>
      set((state) => ({ rightPaneVisible: !state.rightPaneVisible })),
  },
}));
