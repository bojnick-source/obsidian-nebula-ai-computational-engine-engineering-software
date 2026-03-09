import { create } from "zustand";
import type { Collection, CollectionItem } from "../types/collection";
import {
  listCollections,
  createCollection,
  updateCollection,
  deleteCollection,
  getCollectionItems,
  addToCollection,
  removeFromCollection,
  reorderCollectionItem,
} from "../ipc/commands";

interface CollectionState {
  collections: Collection[];
  selectedCollectionId: string | null;
  items: CollectionItem[];
  isLoading: boolean;
  error: string | null;

  actions: {
    loadCollections: () => Promise<void>;
    selectCollection: (id: string | null) => Promise<void>;
    createCollection: (name: string, description: string) => Promise<Collection>;
    updateCollection: (
      id: string,
      name: string,
      description: string,
      coverAssetId: string | null
    ) => Promise<void>;
    deleteCollection: (id: string) => Promise<void>;
    addAsset: (assetId: string, slideNotes?: string) => Promise<void>;
    removeAsset: (assetId: string) => Promise<void>;
    reorderItem: (assetId: string, position: number) => Promise<void>;
  };
}

export const useCollectionStore = create<CollectionState>((set, get) => ({
  collections: [],
  selectedCollectionId: null,
  items: [],
  isLoading: false,
  error: null,

  actions: {
    loadCollections: async () => {
      set({ isLoading: true, error: null });
      try {
        const collections = await listCollections();
        set({ collections, isLoading: false });
      } catch (err) {
        set({ isLoading: false, error: String(err) });
      }
    },

    selectCollection: async (id) => {
      set({ selectedCollectionId: id, items: [] });
      if (!id) return;
      try {
        const items = await getCollectionItems(id);
        set({ items });
      } catch (err) {
        set({ error: String(err) });
      }
    },

    createCollection: async (name, description) => {
      const collection = await createCollection(name, description);
      set((state) => ({ collections: [collection, ...state.collections] }));
      return collection;
    },

    updateCollection: async (id, name, description, coverAssetId) => {
      const updated = await updateCollection(id, name, description, coverAssetId);
      set((state) => ({
        collections: state.collections.map((c) => (c.id === id ? updated : c)),
      }));
    },

    deleteCollection: async (id) => {
      await deleteCollection(id);
      set((state) => ({
        collections: state.collections.filter((c) => c.id !== id),
        selectedCollectionId:
          state.selectedCollectionId === id ? null : state.selectedCollectionId,
        items: state.selectedCollectionId === id ? [] : state.items,
      }));
    },

    addAsset: async (assetId, slideNotes = "") => {
      const { selectedCollectionId } = get();
      if (!selectedCollectionId) return;
      await addToCollection(selectedCollectionId, assetId, slideNotes);
      const items = await getCollectionItems(selectedCollectionId);
      set((state) => ({
        items,
        collections: state.collections.map((c) =>
          c.id === selectedCollectionId
            ? { ...c, itemCount: c.itemCount + 1 }
            : c
        ),
      }));
    },

    removeAsset: async (assetId) => {
      const { selectedCollectionId } = get();
      if (!selectedCollectionId) return;
      await removeFromCollection(selectedCollectionId, assetId);
      set((state) => ({
        items: state.items.filter((i) => i.assetId !== assetId),
        collections: state.collections.map((c) =>
          c.id === selectedCollectionId
            ? { ...c, itemCount: Math.max(0, c.itemCount - 1) }
            : c
        ),
      }));
    },

    reorderItem: async (assetId, position) => {
      const { selectedCollectionId } = get();
      if (!selectedCollectionId) return;
      await reorderCollectionItem(selectedCollectionId, assetId, position);
      set((state) => ({
        items: state.items
          .map((i) => (i.assetId === assetId ? { ...i, position } : i))
          .sort((a, b) => a.position - b.position),
      }));
    },
  },
}));
