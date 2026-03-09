import { useEffect } from "react";
import ReactDOM from "react-dom";
import { useUIStore } from "../../store/useUIStore";
import { useCollectionStore } from "../../store/useCollectionStore";
import { useVaultStore } from "../../store/useVaultStore";
import { PresentationControls } from "./PresentationControls";
import { ViewerPluginHost } from "../viewer/ViewerPluginHost";
import { importanceColor } from "../vault/ImportanceChip";

export function PresentationOverlay() {
  const presentationOpen = useUIStore((s) => s.presentationOpen);
  const collectionId = useUIStore((s) => s.presentationCollectionId);
  const slideIndex = useUIStore((s) => s.presentationSlideIndex);

  const collections = useCollectionStore((s) => s.collections);
  const items = useCollectionStore((s) => s.items);
  const selectedId = useCollectionStore((s) => s.selectedCollectionId);
  const { selectCollection } = useCollectionStore((s) => s.actions);

  const assets = useVaultStore((s) => s.assets);

  // Load collection items when presentation opens
  useEffect(() => {
    if (presentationOpen && collectionId && selectedId !== collectionId) {
      selectCollection(collectionId);
    }
  }, [presentationOpen, collectionId, selectedId, selectCollection]);

  if (!presentationOpen || !collectionId) return null;

  const collection = collections.find((c) => c.id === collectionId);
  const sortedItems = [...items].sort((a, b) => a.position - b.position);
  const total = sortedItems.length;
  const currentItem = sortedItems[slideIndex];
  const currentAsset = currentItem ? assets[currentItem.assetId] : null;

  if (total === 0 || !collection) return null;

  const overlay = (
    <div
      className="fixed inset-0 z-50 flex flex-col"
      style={{ background: "#080808" }}
    >
      <PresentationControls
        currentIndex={slideIndex}
        total={total}
        collectionName={collection.name}
      />

      {/* Main content area */}
      <div className="flex-1 flex flex-col items-center justify-center min-h-0 px-20 py-16">
        {currentAsset ? (
          <>
            {/* Asset viewer */}
            <div
              className="w-full max-w-5xl flex-1 min-h-0 rounded-xl overflow-hidden"
              style={{
                border: `1px solid ${importanceColor(currentAsset.importance)}22`,
                background: "rgba(255,255,255,0.02)",
              }}
            >
              <ViewerPluginHost
                asset={currentAsset}
                
              />
            </div>

            {/* Slide footer: title + notes */}
            <div className="w-full max-w-5xl mt-5 flex items-start justify-between gap-8">
              <div>
                <h2 className="text-white/90 text-xl font-medium leading-tight">
                  {currentAsset.title}
                </h2>
                <p className="text-white/30 text-sm mt-1">
                  <span
                    className="inline-block w-2 h-2 rounded-full mr-1.5 align-middle"
                    style={{ background: importanceColor(currentAsset.importance) }}
                  />
                  {currentAsset.importance}
                  {currentAsset.project && (
                    <span className="ml-3 text-white/20">
                      {currentAsset.project}
                    </span>
                  )}
                </p>
              </div>
              {currentItem?.slideNotes && (
                <p className="text-white/40 text-sm max-w-sm text-right leading-relaxed">
                  {currentItem.slideNotes}
                </p>
              )}
            </div>
          </>
        ) : (
          <p className="text-white/30 text-sm">Asset not found</p>
        )}
      </div>
    </div>
  );

  return ReactDOM.createPortal(overlay, document.body);
}
