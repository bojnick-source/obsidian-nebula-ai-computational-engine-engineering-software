import { create } from "zustand";
import {
  startForgeListener,
  stopForgeListener,
  setApiKey,
  getApiKeyStatus,
  classifyAsset,
} from "../ipc/commands";
import type { AssetRecord } from "../types/asset";

interface ForgeState {
  listenerRunning: boolean;
  listenerConnected: boolean; // ZMQ socket actually connected to FORGE
  hasApiKey: boolean;
  isClassifying: boolean;
  classifyError: string | null;
  lastIngestedAsset: AssetRecord | null;

  actions: {
    checkApiKeyStatus: () => Promise<void>;
    saveApiKey: (key: string) => Promise<void>;
    startListener: (endpoint?: string) => Promise<void>;
    stopListener: () => Promise<void>;
    classifyAsset: (id: string, apiKey?: string) => Promise<AssetRecord>;
    setListenerConnected: (connected: boolean) => void;
    setLastIngestedAsset: (asset: AssetRecord) => void;
  };
}

export const useForgeStore = create<ForgeState>((set) => ({
  listenerRunning: false,
  listenerConnected: false,
  hasApiKey: false,
  isClassifying: false,
  classifyError: null,
  lastIngestedAsset: null,

  actions: {
    checkApiKeyStatus: async () => {
      const has = await getApiKeyStatus();
      set({ hasApiKey: has });
    },

    saveApiKey: async (key) => {
      await setApiKey(key);
      set({ hasApiKey: key.length > 0 });
    },

    startListener: async (endpoint) => {
      await startForgeListener(endpoint);
      set({ listenerRunning: true });
    },

    stopListener: async () => {
      await stopForgeListener();
      set({ listenerRunning: false, listenerConnected: false });
    },

    classifyAsset: async (id, apiKey) => {
      set({ isClassifying: true, classifyError: null });
      try {
        const enriched = await classifyAsset(id, apiKey);
        set({ isClassifying: false });
        return enriched;
      } catch (err) {
        set({ isClassifying: false, classifyError: String(err) });
        throw err;
      }
    },

    setListenerConnected: (connected) => set({ listenerConnected: connected }),
    setLastIngestedAsset: (asset) => set({ lastIngestedAsset: asset }),
  },
}));
