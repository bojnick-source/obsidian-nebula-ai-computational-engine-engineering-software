import { create } from "zustand";
import type { AssetRecord } from "../types/asset";
import { searchAssets } from "../ipc/commands";

interface SearchState {
  query: string;
  results: AssetRecord[];
  isSearching: boolean;
  isActive: boolean;
  actions: {
    setQuery: (query: string) => void;
    executeSearch: (query: string) => Promise<void>;
    clearSearch: () => void;
  };
}

export const useSearchStore = create<SearchState>((set) => ({
  query: "",
  results: [],
  isSearching: false,
  isActive: false,

  actions: {
    setQuery: (query) => set({ query }),

    executeSearch: async (query) => {
      if (!query.trim()) {
        set({ results: [], isActive: false, isSearching: false });
        return;
      }
      set({ isSearching: true, isActive: true });
      try {
        const results = await searchAssets(query);
        set({ results, isSearching: false });
      } catch {
        set({ isSearching: false, results: [] });
      }
    },

    clearSearch: () =>
      set({ query: "", results: [], isSearching: false, isActive: false }),
  },
}));
