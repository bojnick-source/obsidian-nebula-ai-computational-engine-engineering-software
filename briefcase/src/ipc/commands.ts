import { invoke } from "@tauri-apps/api/core";
import { convertFileSrc } from "@tauri-apps/api/core";
import type { AssetRecord, AssetRelationship } from "../types/asset";
import type { AssetFilter, AssetPatch } from "../types/filters";

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
  // Convert the filesystem path to a tauri-safe URL
  return convertFileSrc(filePath);
};

export const verifyIntegrity = (contentHash: string): Promise<boolean> =>
  invoke("verify_integrity", { contentHash });

export const updateAssetMetadata = (
  id: string,
  patch: AssetPatch
): Promise<AssetRecord> => invoke("update_asset_metadata", { id, patch });
