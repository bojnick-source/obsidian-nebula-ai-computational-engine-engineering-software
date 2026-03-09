import { create } from "zustand";

interface UIState {
  previewOpen: boolean;
  previewAssetId: string | null;
  rightPaneVisible: boolean;
  // Presentation mode
  presentationOpen: boolean;
  presentationCollectionId: string | null;
  presentationSlideIndex: number;
  // Settings panel
  settingsOpen: boolean;

  actions: {
    openPreview: (assetId: string) => void;
    closePreview: () => void;
    toggleRightPane: () => void;
    openPresentation: (collectionId: string) => void;
    closePresentation: () => void;
    setSlideIndex: (index: number) => void;
    nextSlide: (total: number) => void;
    prevSlide: () => void;
    toggleSettings: () => void;
  };
}

export const useUIStore = create<UIState>((set, get) => ({
  previewOpen: false,
  previewAssetId: null,
  rightPaneVisible: true,
  presentationOpen: false,
  presentationCollectionId: null,
  presentationSlideIndex: 0,
  settingsOpen: false,

  actions: {
    openPreview: (assetId) =>
      set({ previewOpen: true, previewAssetId: assetId }),

    closePreview: () =>
      set({ previewOpen: false, previewAssetId: null }),

    toggleRightPane: () =>
      set((state) => ({ rightPaneVisible: !state.rightPaneVisible })),

    openPresentation: (collectionId) =>
      set({ presentationOpen: true, presentationCollectionId: collectionId, presentationSlideIndex: 0 }),

    closePresentation: () =>
      set({ presentationOpen: false, presentationCollectionId: null }),

    setSlideIndex: (index) => set({ presentationSlideIndex: index }),

    nextSlide: (total) => {
      const { presentationSlideIndex } = get();
      if (presentationSlideIndex < total - 1) {
        set({ presentationSlideIndex: presentationSlideIndex + 1 });
      }
    },

    prevSlide: () => {
      const { presentationSlideIndex } = get();
      if (presentationSlideIndex > 0) {
        set({ presentationSlideIndex: presentationSlideIndex - 1 });
      }
    },

    toggleSettings: () =>
      set((state) => ({ settingsOpen: !state.settingsOpen })),
  },
}));
