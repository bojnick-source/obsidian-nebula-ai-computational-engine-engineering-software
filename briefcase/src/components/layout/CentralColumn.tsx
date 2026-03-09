import { useVaultStore } from "../../store/useVaultStore";
import { useSearchStore } from "../../store/useSearchStore";
import { DrawerGroup } from "../vault/DrawerGroup";
import { FileCard } from "../vault/FileCard";
import { SearchBar } from "../search/SearchBar";
import { DropZone } from "../vault/DropZone";
import { open } from "@tauri-apps/plugin-dialog";

export function CentralColumn() {
  const drawerGroups = useVaultStore((s) => s.drawerGroups);
  const isLoading = useVaultStore((s) => s.isLoading);
  const assetCount = useVaultStore((s) => s.assetOrder.length);
  const { ingestFiles } = useVaultStore((s) => s.actions);

  const isSearchActive = useSearchStore((s) => s.isActive);
  const searchResults = useSearchStore((s) => s.results);
  const searchQuery = useSearchStore((s) => s.query);

  const handleImportClick = async () => {
    const selected = await open({
      multiple: true,
      directory: false,
    });
    if (!selected) return;
    const paths = Array.isArray(selected) ? selected : [selected];
    await ingestFiles(paths);
  };

  return (
    <div className="flex flex-col h-full overflow-hidden">
      {/* Toolbar */}
      <div
        className="flex items-center gap-3 px-4 py-3 shrink-0"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}
      >
        <div className="flex-1">
          <SearchBar />
        </div>
        <button
          onClick={handleImportClick}
          className="flex items-center gap-1.5 px-3 py-2 rounded-lg text-xs font-medium text-blue-400 hover:text-blue-300 transition-colors shrink-0"
          style={{
            background: "rgba(59,130,246,0.1)",
            border: "1px solid rgba(59,130,246,0.2)",
          }}
        >
          <span>+</span> Import
        </button>
      </div>

      {/* Content area with drop zone */}
      <DropZone>
        <div className="h-full overflow-y-auto px-4 py-4">
          {isLoading && assetCount === 0 ? (
            <div className="flex items-center justify-center h-32">
              <div className="w-6 h-6 border-2 border-blue-500/30 border-t-blue-500 rounded-full animate-spin" />
            </div>
          ) : isSearchActive ? (
            /* Search results view */
            <div>
              <p className="text-white/30 text-xs mb-3">
                {searchResults.length} results for "{searchQuery}"
              </p>
              <div
                className="grid gap-2"
                style={{
                  gridTemplateColumns: "repeat(auto-fill, minmax(140px, 1fr))",
                }}
              >
                {searchResults.map((asset) => (
                  <FileCard key={asset.id} asset={asset} />
                ))}
                {searchResults.length === 0 && (
                  <div className="col-span-full flex flex-col items-center py-12 text-center">
                    <span className="text-3xl mb-3 opacity-30">🔍</span>
                    <p className="text-white/30 text-sm">No results found</p>
                    <p className="text-white/15 text-xs mt-1">
                      Try different keywords
                    </p>
                  </div>
                )}
              </div>
            </div>
          ) : assetCount === 0 ? (
            /* Empty state */
            <div className="flex flex-col items-center justify-center h-64 text-center px-8">
              <span className="text-5xl mb-4 opacity-30">💼</span>
              <p className="text-white/40 font-medium text-sm">
                Your vault is empty
              </p>
              <p className="text-white/20 text-xs mt-2 max-w-xs">
                Drag files here or click Import to add your first deliverables
              </p>
              <button
                onClick={handleImportClick}
                className="mt-6 px-4 py-2 rounded-lg text-xs font-medium text-blue-400 transition-colors"
                style={{
                  background: "rgba(59,130,246,0.1)",
                  border: "1px solid rgba(59,130,246,0.2)",
                }}
              >
                Import files
              </button>
            </div>
          ) : (
            /* Vault drawers */
            <div className="flex flex-col gap-2">
              {drawerGroups.map((group) => (
                <DrawerGroup key={group.key} group={group} />
              ))}
            </div>
          )}
        </div>
      </DropZone>
    </div>
  );
}
