import { useEffect } from "react";
import { listen } from "@tauri-apps/api/event";
import { Shell } from "./components/layout/Shell";
import { useAssets } from "./hooks/useAssets";
import { useCollectionStore } from "./store/useCollectionStore";
import { useForgeStore } from "./store/useForgeStore";
import { useVaultStore } from "./store/useVaultStore";
import type { AssetRecord } from "./types/asset";

export default function App() {
  // Initialize asset + collection loading on mount
  useAssets();
  const { loadCollections } = useCollectionStore((s) => s.actions);
  const { checkApiKeyStatus, setListenerConnected, setLastIngestedAsset } =
    useForgeStore((s) => s.actions);
  const { loadAssets } = useVaultStore((s) => s.actions);

  useEffect(() => {
    loadCollections();
    checkApiKeyStatus();
  }, [loadCollections, checkApiKeyStatus]);

  // Listen for FORGE background events
  useEffect(() => {
    const unlistenIngested = listen<AssetRecord>(
      "forge://asset-ingested",
      (event) => {
        setLastIngestedAsset(event.payload);
        loadAssets(); // refresh the asset list
      }
    );

    const unlistenStatus = listen<boolean>(
      "forge://listener-status",
      (event) => {
        setListenerConnected(event.payload);
      }
    );

    return () => {
      unlistenIngested.then((fn) => fn());
      unlistenStatus.then((fn) => fn());
    };
  }, [setLastIngestedAsset, setListenerConnected, loadAssets]);

  return <Shell />;
}
