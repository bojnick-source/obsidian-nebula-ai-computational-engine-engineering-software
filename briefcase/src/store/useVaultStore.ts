import { create } from "zustand";
import type { AssetRecord, DrawerGroup } from "../types/asset";
import { listAssets, ingestFile } from "../ipc/commands";

type GroupBy = "project" | "fileType" | "importance" | "recency";

interface VaultState {
  assets: Record<string, AssetRecord>;
  assetOrder: string[];
  selectedId: string | null;
  drawerGroups: DrawerGroup[];
  groupBy: GroupBy;
  showArchived: boolean;
  isLoading: boolean;
  error: string | null;
  actions: {
    loadAssets: () => Promise<void>;
    selectAsset: (id: string | null) => void;
    ingestFiles: (filePaths: string[]) => Promise<void>;
    toggleDrawer: (key: string) => void;
    setGroupBy: (groupBy: GroupBy) => void;
    toggleShowArchived: () => void;
  };
}

function buildDrawerGroups(
  assets: AssetRecord[],
  groupBy: GroupBy,
  showArchived: boolean
): DrawerGroup[] {
  const visible = showArchived
    ? assets
    : assets.filter((a) => a.importance !== "archived");

  const groups: Map<string, DrawerGroup> = new Map();

  for (const asset of visible) {
    let key: string;
    let label: string;

    switch (groupBy) {
      case "project":
        key = asset.project ?? "__unassigned__";
        label = asset.project ?? "Unassigned";
        break;
      case "fileType": {
        const mime = asset.fileType.split("/")[0] ?? "other";
        key = mime;
        label = mime.charAt(0).toUpperCase() + mime.slice(1);
        break;
      }
      case "importance":
        key = asset.importance;
        label = asset.importance.charAt(0).toUpperCase() + asset.importance.slice(1);
        break;
      case "recency": {
        const date = new Date(asset.ingestedAt);
        const now = new Date();
        const diffDays = Math.floor(
          (now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24)
        );
        if (diffDays < 7) {
          key = "last-7d";
          label = "Last 7 days";
        } else if (diffDays < 30) {
          key = "last-30d";
          label = "Last 30 days";
        } else {
          key = "older";
          label = "Older";
        }
        break;
      }
    }

    if (!groups.has(key)) {
      groups.set(key, {
        key,
        label,
        importance: groupBy === "importance" ? asset.importance : undefined,
        assetIds: [],
        isOpen: true,
      });
    }
    groups.get(key)!.assetIds.push(asset.id);
  }

  return Array.from(groups.values());
}

export const useVaultStore = create<VaultState>((set, get) => ({
  assets: {},
  assetOrder: [],
  selectedId: null,
  drawerGroups: [],
  groupBy: "project",
  showArchived: false,
  isLoading: false,
  error: null,

  actions: {
    loadAssets: async () => {
      set({ isLoading: true, error: null });
      try {
        const assets = await listAssets({});
        const assetMap: Record<string, AssetRecord> = {};
        for (const a of assets) {
          assetMap[a.id] = a;
        }
        const { groupBy, showArchived } = get();
        const groups = buildDrawerGroups(assets, groupBy, showArchived);
        set({
          assets: assetMap,
          assetOrder: assets.map((a) => a.id),
          drawerGroups: groups,
          isLoading: false,
        });
      } catch (err) {
        set({ isLoading: false, error: String(err) });
      }
    },

    selectAsset: (id) => set({ selectedId: id }),

    ingestFiles: async (filePaths) => {
      set({ isLoading: true, error: null });
      try {
        const newAssets: AssetRecord[] = [];
        for (const fp of filePaths) {
          const asset = await ingestFile(fp);
          newAssets.push(asset);
        }
        // Merge new assets into state
        set((state) => {
          const updated = { ...state.assets };
          for (const a of newAssets) {
            updated[a.id] = a;
          }
          const allAssets = Object.values(updated);
          const groups = buildDrawerGroups(
            allAssets,
            state.groupBy,
            state.showArchived
          );
          return {
            assets: updated,
            assetOrder: allAssets.map((a) => a.id),
            drawerGroups: groups,
            isLoading: false,
          };
        });
      } catch (err) {
        set({ isLoading: false, error: String(err) });
      }
    },

    toggleDrawer: (key) => {
      set((state) => ({
        drawerGroups: state.drawerGroups.map((g) =>
          g.key === key ? { ...g, isOpen: !g.isOpen } : g
        ),
      }));
    },

    setGroupBy: (groupBy) => {
      set((state) => {
        const assets = Object.values(state.assets);
        const groups = buildDrawerGroups(assets, groupBy, state.showArchived);
        return { groupBy, drawerGroups: groups };
      });
    },

    toggleShowArchived: () => {
      set((state) => {
        const showArchived = !state.showArchived;
        const assets = Object.values(state.assets);
        const groups = buildDrawerGroups(assets, state.groupBy, showArchived);
        return { showArchived, drawerGroups: groups };
      });
    },
  },
}));
