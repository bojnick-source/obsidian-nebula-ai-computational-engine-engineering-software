import { useState } from "react";
import { useCollectionStore } from "../../store/useCollectionStore";
import { useUIStore } from "../../store/useUIStore";
import type { Collection } from "../../types/collection";

export function CollectionSidebar() {
  const collections = useCollectionStore((s) => s.collections);
  const selectedId = useCollectionStore((s) => s.selectedCollectionId);
  const { selectCollection, createCollection } = useCollectionStore((s) => s.actions);
  const { openPresentation } = useUIStore((s) => s.actions);

  const [creating, setCreating] = useState(false);
  const [newName, setNewName] = useState("");

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault();
    if (!newName.trim()) return;
    await createCollection(newName.trim(), "");
    setNewName("");
    setCreating(false);
  }

  return (
    <section>
      <div className="flex items-center justify-between px-1 mb-2">
        <p className="text-white/20 text-[10px] uppercase tracking-widest">
          Collections
        </p>
        <button
          onClick={() => setCreating(true)}
          className="text-white/20 hover:text-white/60 text-xs transition-colors"
          title="New collection"
        >
          +
        </button>
      </div>

      {creating && (
        <form onSubmit={handleCreate} className="mb-2 px-1">
          <input
            autoFocus
            value={newName}
            onChange={(e) => setNewName(e.target.value)}
            onKeyDown={(e) => e.key === "Escape" && setCreating(false)}
            placeholder="Collection name…"
            className="w-full bg-white/[0.06] text-white/80 text-xs rounded px-2 py-1.5 outline-none border border-white/10 focus:border-white/20"
          />
        </form>
      )}

      <div className="flex flex-col gap-0.5">
        {collections.map((c) => (
          <CollectionRow
            key={c.id}
            collection={c}
            isSelected={selectedId === c.id}
            onSelect={() => selectCollection(c.id)}
            onPresent={() => openPresentation(c.id)}
          />
        ))}
        {collections.length === 0 && !creating && (
          <p className="text-white/15 text-[10px] px-3 py-1">No collections yet</p>
        )}
      </div>
    </section>
  );
}

function CollectionRow({
  collection,
  isSelected,
  onSelect,
  onPresent,
}: {
  collection: Collection;
  isSelected: boolean;
  onSelect: () => void;
  onPresent: () => void;
}) {
  return (
    <div
      className={`group flex items-center gap-1 px-3 py-1.5 rounded-lg cursor-pointer transition-colors ${
        isSelected
          ? "bg-white/10 text-white/90"
          : "text-white/40 hover:text-white/70 hover:bg-white/[0.04]"
      }`}
      onClick={onSelect}
    >
      <span className="text-white/30 text-xs">▤</span>
      <span className="flex-1 text-xs truncate">{collection.name}</span>
      <span className="text-white/20 text-[10px] tabular-nums">
        {collection.itemCount}
      </span>
      {collection.itemCount > 0 && (
        <button
          onClick={(e) => {
            e.stopPropagation();
            onPresent();
          }}
          className="opacity-0 group-hover:opacity-100 text-white/30 hover:text-white/70 text-[10px] transition-all ml-1"
          title="Present"
        >
          ▶
        </button>
      )}
    </div>
  );
}
