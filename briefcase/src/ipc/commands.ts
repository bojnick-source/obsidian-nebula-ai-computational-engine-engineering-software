import { invoke, convertFileSrc } from "@tauri-apps/api/core";
import type { AssetRecord, AssetRelationship } from "../types/asset";
import type { AssetFilter, AssetPatch } from "../types/filters";
import type { Collection, CollectionItem } from "../types/collection";

// ── Phase 1 ───────────────────────────────────────────────────────────────────

export const ingestFile = (filePath: string): Promise<AssetRecord> =>
  invoke("ingest_file", { filePath });

export const getAsset = (id: string): Promise<AssetRecord> =>
  invoke("get_asset", { id });

export const listAssets = (filter: AssetFilter = {}): Promise<AssetRecord[]> =>
  invoke("list_assets", { filter });

export const searchAssets = (query: string): Promise<AssetRecord[]> =>
  invoke("search_assets", { query });

export const getRelationships = (
  assetId: string
): Promise<AssetRelationship[]> => invoke("get_relationships", { assetId });

export const getFileUrl = async (contentHash: string): Promise<string> => {
  const filePath: string = await invoke("get_file_url", { contentHash });
  return convertFileSrc(filePath);
};

export const verifyIntegrity = (contentHash: string): Promise<boolean> =>
  invoke("verify_integrity", { contentHash });

export const updateAssetMetadata = (
  id: string,
  patch: AssetPatch
): Promise<AssetRecord> => invoke("update_asset_metadata", { id, patch });

// ── Phase 2: FORGE listener & LLM ────────────────────────────────────────────

export const startForgeListener = (endpoint?: string): Promise<void> =>
  invoke("start_forge_listener", { endpoint });

export const stopForgeListener = (): Promise<void> =>
  invoke("stop_forge_listener");

export const getForgeListenerStatus = (): Promise<boolean> =>
  invoke("get_forge_listener_status");

export const setApiKey = (apiKey: string): Promise<void> =>
  invoke("set_api_key", { apiKey });

export const getApiKeyStatus = (): Promise<boolean> =>
  invoke("get_api_key_status");

export const classifyAsset = (
  id: string,
  apiKey?: string
): Promise<AssetRecord> => invoke("classify_asset", { id, apiKey });

// ── Phase 2: Collections ──────────────────────────────────────────────────────

export const createCollection = (
  name: string,
  description: string
): Promise<Collection> => invoke("create_collection", { name, description });

export const updateCollection = (
  id: string,
  name: string,
  description: string,
  coverAssetId: string | null
): Promise<Collection> =>
  invoke("update_collection", { id, name, description, coverAssetId });

export const deleteCollection = (id: string): Promise<void> =>
  invoke("delete_collection", { id });

export const listCollections = (): Promise<Collection[]> =>
  invoke("list_collections");

export const getCollectionItems = (
  collectionId: string
): Promise<CollectionItem[]> =>
  invoke("get_collection_items", { collectionId });

export const addToCollection = (
  collectionId: string,
  assetId: string,
  slideNotes: string
): Promise<void> =>
  invoke("add_to_collection", { collectionId, assetId, slideNotes });

export const removeFromCollection = (
  collectionId: string,
  assetId: string
): Promise<void> => invoke("remove_from_collection", { collectionId, assetId });

export const reorderCollectionItem = (
  collectionId: string,
  assetId: string,
  position: number
): Promise<void> =>
  invoke("reorder_collection_item", { collectionId, assetId, position });
