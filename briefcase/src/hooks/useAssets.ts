import { useEffect } from "react";
import { useVaultStore } from "../store/useVaultStore";

export function useAssets() {
  const assets = useVaultStore((s) => s.assets);
  const assetOrder = useVaultStore((s) => s.assetOrder);
  const isLoading = useVaultStore((s) => s.isLoading);
  const error = useVaultStore((s) => s.error);
  const { loadAssets } = useVaultStore((s) => s.actions);

  useEffect(() => {
    loadAssets();
  }, [loadAssets]);

  return {
    assets,
    assetOrder,
    isLoading,
    error,
    loadAssets,
  };
}
