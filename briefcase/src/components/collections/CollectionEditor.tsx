import { useState, useEffect } from "react";
import { useCollectionStore } from "../../store/useCollectionStore";
import { useVaultStore } from "../../store/useVaultStore";
import { useUIStore } from "../../store/useUIStore";

export function CollectionEditor() {
  const collections = useCollectionStore((s) => s.collections);
  const selectedId = useCollectionStore((s) => s.selectedCollectionId);
  const items = useCollectionStore((s) => s.items);
  const { updateCollection, deleteCollection, addAsset, removeAsset } =
    useCollectionStore((s) => s.actions);
  const { openPresentation } = useUIStore((s) => s.actions);

  const assets = useVaultStore((s) => s.assets);
  const selectedAssetId = useVaultStore((s) => s.selectedId);

  const collection = collections.find((c) => c.id === selectedId);
  const [editingName, setEditingName] = useState(false);
  const [name, setName] = useState(collection?.name ?? "");

  useEffect(() => {
    if (collection) {
      setName(collection.name);
    }
  }, [collection]);

  if (!collection) return null;

  async function saveName() {
    if (!collection) return;
    setEditingName(false);
    if (name.trim() && name !== collection.name) {
      await updateCollection(collection.id, name.trim(), collection.description, collection.coverAssetId);
    }
  }

  async function handleAddSelected() {
    if (!selectedAssetId || items.some((i) => i.assetId === selectedAssetId)) return;
    await addAsset(selectedAssetId);
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div
        className="px-4 pt-4 pb-3 shrink-0"
        style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}
      >
        {editingName ? (
          <input
            autoFocus
            value={name}
            onChange={(e) => setName(e.target.value)}
            onBlur={saveName}
            onKeyDown={(e) => e.key === "Enter" && saveName()}
            className="w-full bg-transparent text-white/90 text-sm font-medium outline-none border-b border-white/20"
          />
        ) : (
          <button
            onClick={() => setEditingName(true)}
            className="text-white/90 text-sm font-medium text-left hover:text-white transition-colors"
          >
            {collection.name}
          </button>
        )}
        <p className="text-white/20 text-[10px] mt-1">
          {collection.itemCount} slide{collection.itemCount !== 1 ? "s" : ""}
        </p>
      </div>

      {/* Actions */}
      <div className="flex gap-2 px-4 py-2 shrink-0">
        {collection.itemCount > 0 && (
          <button
            onClick={() => openPresentation(collection.id)}
            className="flex-1 text-xs py-1.5 rounded-lg bg-white/10 text-white/80 hover:bg-white/15 transition-colors"
          >
            ▶ Present
          </button>
        )}
        {selectedAssetId && !items.some((i) => i.assetId === selectedAssetId) && (
          <button
            onClick={handleAddSelected}
            className="flex-1 text-xs py-1.5 rounded-lg bg-white/[0.06] text-white/50 hover:bg-white/10 hover:text-white/70 transition-colors"
          >
            + Add selected
          </button>
        )}
      </div>

      {/* Slide list */}
      <div className="flex-1 overflow-y-auto px-4 py-2 flex flex-col gap-1">
        {items.map((item, index) => (
          <SlideRow
            key={item.assetId}
            index={index}
            title={assets[item.assetId]?.title ?? item.assetId}
            onRemove={() => removeAsset(item.assetId)}
          />
        ))}
        {items.length === 0 && (
          <p className="text-white/20 text-xs text-center py-8">
            Select an asset and click "Add selected"
          </p>
        )}
      </div>

      {/* Danger zone */}
      <div className="px-4 py-3 shrink-0" style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}>
        <button
          onClick={async () => {
            if (confirm(`Delete "${collection.name}"?`)) {
              await deleteCollection(collection.id);
            }
          }}
          className="text-red-400/40 hover:text-red-400/70 text-xs transition-colors"
        >
          Delete collection
        </button>
      </div>
    </div>
  );
}

function SlideRow({
  index,
  title,
  onRemove,
}: {
  index: number;
  title: string;
  onRemove: () => void;
}) {
  return (
    <div className="group flex items-center gap-2 px-3 py-2 rounded-lg bg-white/[0.03] hover:bg-white/[0.06] transition-colors">
      <span className="text-white/20 text-[10px] tabular-nums w-4 shrink-0">
        {index + 1}
      </span>
      <span className="flex-1 text-xs text-white/60 truncate">{title}</span>
      <button
        onClick={onRemove}
        className="opacity-0 group-hover:opacity-100 text-white/20 hover:text-red-400/60 text-xs transition-all"
      >
        ✕
      </button>
    </div>
  );
}
