import { LeftRail } from "./LeftRail";
import { CentralColumn } from "./CentralColumn";
import { RightPane } from "./RightPane";
import { PreviewOverlay } from "../viewer/PreviewOverlay";
import { PresentationOverlay } from "../presentation/PresentationOverlay";
import { ForgeSettingsPanel } from "../forge/ForgeSettingsPanel";
import { useUIStore } from "../../store/useUIStore";

export function Shell() {
  const { toggleRightPane } = useUIStore((s) => s.actions);
  const rightPaneVisible = useUIStore((s) => s.rightPaneVisible);
  const settingsOpen = useUIStore((s) => s.settingsOpen);

  return (
    <div
      className="flex h-screen overflow-hidden"
      style={{ background: "#0f0f0f" }}
    >
      {/* Left rail */}
      <div
        className="shrink-0"
        style={{
          width: 220,
          background: "rgba(255,255,255,0.02)",
        }}
      >
        <LeftRail />
      </div>

      {/* Main content */}
      <div className="flex-1 min-w-0 flex flex-col overflow-hidden">
        {/* Top bar */}
        <div
          className="flex items-center justify-end px-3 py-1.5 shrink-0"
          style={{ borderBottom: "1px solid rgba(255,255,255,0.04)" }}
        >
          <button
            onClick={toggleRightPane}
            className="text-white/30 hover:text-white/60 text-xs px-2 py-1 rounded transition-colors"
            title={rightPaneVisible ? "Hide details" : "Show details"}
          >
            {rightPaneVisible ? "⊞" : "⊟"} Details
          </button>
        </div>

        {/* Content row */}
        <div className="flex-1 min-h-0 flex overflow-hidden">
          <div className="flex-1 min-w-0 overflow-hidden">
            <CentralColumn />
          </div>
          <RightPane />
        </div>
      </div>

      {/* Overlays */}
      <PreviewOverlay />
      <PresentationOverlay />
      {settingsOpen && <ForgeSettingsPanel />}
    </div>
  );
}
