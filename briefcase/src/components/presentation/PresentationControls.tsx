import { useEffect } from "react";
import { useUIStore } from "../../store/useUIStore";

interface Props {
  currentIndex: number;
  total: number;
  collectionName: string;
}

export function PresentationControls({ currentIndex, total, collectionName }: Props) {
  const { nextSlide, prevSlide, closePresentation } = useUIStore((s) => s.actions);

  // Keyboard navigation
  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      if (e.key === "ArrowRight" || e.key === "ArrowDown" || e.key === " ") {
        e.preventDefault();
        nextSlide(total);
      } else if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
        e.preventDefault();
        prevSlide();
      } else if (e.key === "Escape") {
        closePresentation();
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [total, nextSlide, prevSlide, closePresentation]);

  return (
    <>
      {/* Top bar */}
      <div
        className="absolute top-0 left-0 right-0 flex items-center justify-between px-6 py-3 z-10"
        style={{ background: "linear-gradient(to bottom, rgba(0,0,0,0.7), transparent)" }}
      >
        <span className="text-white/40 text-sm truncate max-w-xs">{collectionName}</span>
        <div className="flex items-center gap-4">
          <span className="text-white/30 text-sm tabular-nums">
            {currentIndex + 1} / {total}
          </span>
          <button
            onClick={closePresentation}
            className="text-white/30 hover:text-white/80 text-lg transition-colors"
            title="Close (Esc)"
          >
            ✕
          </button>
        </div>
      </div>

      {/* Progress bar */}
      <div
        className="absolute top-0 left-0 h-[2px] bg-white/20 transition-all duration-300"
        style={{ width: `${((currentIndex + 1) / total) * 100}%` }}
      />

      {/* Left/Right navigation arrows */}
      {currentIndex > 0 && (
        <button
          onClick={prevSlide}
          className="absolute left-4 top-1/2 -translate-y-1/2 text-white/20 hover:text-white/70 text-3xl transition-colors z-10 w-12 h-12 flex items-center justify-center rounded-full hover:bg-white/10"
          title="Previous (←)"
        >
          ‹
        </button>
      )}
      {currentIndex < total - 1 && (
        <button
          onClick={() => nextSlide(total)}
          className="absolute right-4 top-1/2 -translate-y-1/2 text-white/20 hover:text-white/70 text-3xl transition-colors z-10 w-12 h-12 flex items-center justify-center rounded-full hover:bg-white/10"
          title="Next (→)"
        >
          ›
        </button>
      )}

      {/* Dot indicators */}
      {total <= 20 && (
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-1.5 z-10">
          {Array.from({ length: total }).map((_, i) => (
            <button
              key={i}
              onClick={() => useUIStore.getState().actions.setSlideIndex(i)}
              className={`w-1.5 h-1.5 rounded-full transition-all ${
                i === currentIndex ? "bg-white/70 w-3" : "bg-white/20 hover:bg-white/40"
              }`}
            />
          ))}
        </div>
      )}
    </>
  );
}
