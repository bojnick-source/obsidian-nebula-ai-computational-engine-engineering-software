import { useCallback, useEffect, useRef } from "react";
import { useSearchStore } from "../../store/useSearchStore";

export function SearchBar() {
  const query = useSearchStore((s) => s.query);
  const isSearching = useSearchStore((s) => s.isSearching);
  const isActive = useSearchStore((s) => s.isActive);
  const { setQuery, executeSearch, clearSearch } = useSearchStore((s) => s.actions);

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const val = e.target.value;
      setQuery(val);
      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(() => {
        executeSearch(val);
      }, 300);
    },
    [setQuery, executeSearch]
  );

  const handleClear = useCallback(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    clearSearch();
  }, [clearSearch]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Escape") handleClear();
    },
    [handleClear]
  );

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
    };
  }, []);

  return (
    <div className="relative flex items-center">
      <span className="absolute left-3 text-white/30 text-sm pointer-events-none">
        {isSearching ? "⏳" : "🔍"}
      </span>
      <input
        type="text"
        value={query}
        onChange={handleChange}
        onKeyDown={handleKeyDown}
        placeholder="Search files, tags, projects..."
        className="w-full pl-9 pr-9 py-2 text-sm rounded-lg text-white/80 placeholder-white/20 outline-none transition-all"
        style={{
          background: "rgba(255,255,255,0.05)",
          border: `1px solid ${isActive ? "rgba(59,130,246,0.5)" : "rgba(255,255,255,0.08)"}`,
          caretColor: "#3b82f6",
        }}
      />
      {(query || isActive) && (
        <button
          onClick={handleClear}
          className="absolute right-3 text-white/30 hover:text-white/60 text-xs transition-colors"
        >
          ✕
        </button>
      )}
    </div>
  );
}
