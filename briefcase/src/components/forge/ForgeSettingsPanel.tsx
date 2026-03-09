import { useState } from "react";
import { useForgeStore } from "../../store/useForgeStore";
import { useUIStore } from "../../store/useUIStore";
import { useVaultStore } from "../../store/useVaultStore";

export function ForgeSettingsPanel() {
  const listenerRunning = useForgeStore((s) => s.listenerRunning);
  const listenerConnected = useForgeStore((s) => s.listenerConnected);
  const hasApiKey = useForgeStore((s) => s.hasApiKey);
  const isClassifying = useForgeStore((s) => s.isClassifying);
  const { startListener, stopListener, saveApiKey, classifyAsset } = useForgeStore(
    (s) => s.actions
  );
  const { toggleSettings } = useUIStore((s) => s.actions);

  const selectedId = useVaultStore((s) => s.selectedId);
  const { loadAssets } = useVaultStore((s) => s.actions);

  const [apiKeyInput, setApiKeyInput] = useState("");
  const [endpoint, setEndpoint] = useState("tcp://127.0.0.1:5555");
  const [keySaved, setKeySaved] = useState(false);

  async function handleSaveKey() {
    await saveApiKey(apiKeyInput);
    setApiKeyInput("");
    setKeySaved(true);
    setTimeout(() => setKeySaved(false), 2000);
  }

  async function handleClassify() {
    if (!selectedId) return;
    try {
      await classifyAsset(selectedId);
      await loadAssets();
    } catch {
      // error displayed via store
    }
  }

  return (
    <div
      className="fixed inset-0 z-40 flex items-center justify-center"
      style={{ background: "rgba(0,0,0,0.7)" }}
      onClick={toggleSettings}
    >
      <div
        className="relative w-[480px] rounded-2xl p-6 flex flex-col gap-6"
        style={{
          background: "rgba(20,20,22,0.97)",
          border: "1px solid rgba(255,255,255,0.08)",
          backdropFilter: "blur(20px)",
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-center justify-between">
          <h2 className="text-white/90 font-semibold">FORGE Integration</h2>
          <button
            onClick={toggleSettings}
            className="text-white/30 hover:text-white/70 transition-colors"
          >
            ✕
          </button>
        </div>

        {/* ZMQ Listener */}
        <section className="flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-white/70 text-sm">Event Bus Listener</p>
              <p className="text-white/30 text-xs mt-0.5">
                Auto-ingest files on{" "}
                <code className="text-white/40 bg-white/[0.06] px-1 rounded">
                  vault_write
                </code>{" "}
                events
              </p>
            </div>
            <StatusDot active={listenerRunning} connected={listenerConnected} />
          </div>

          <div className="flex gap-2">
            <input
              value={endpoint}
              onChange={(e) => setEndpoint(e.target.value)}
              disabled={listenerRunning}
              className="flex-1 bg-white/[0.06] text-white/60 text-xs rounded-lg px-3 py-2 outline-none border border-white/[0.08] focus:border-white/20 disabled:opacity-40"
              placeholder="tcp://127.0.0.1:5555"
            />
            {listenerRunning ? (
              <button
                onClick={stopListener}
                className="px-3 py-2 text-xs rounded-lg bg-red-500/10 text-red-400/70 hover:bg-red-500/20 transition-colors"
              >
                Stop
              </button>
            ) : (
              <button
                onClick={() => startListener(endpoint)}
                className="px-3 py-2 text-xs rounded-lg bg-white/10 text-white/70 hover:bg-white/15 transition-colors"
              >
                Start
              </button>
            )}
          </div>
        </section>

        <div style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }} />

        {/* Claude API key */}
        <section className="flex flex-col gap-3">
          <div>
            <p className="text-white/70 text-sm">Claude API Key</p>
            <p className="text-white/30 text-xs mt-0.5">
              Enables LLM classification — key stored in memory only
            </p>
          </div>
          <div className="flex gap-2 items-center">
            <input
              type="password"
              value={apiKeyInput}
              onChange={(e) => setApiKeyInput(e.target.value)}
              placeholder={hasApiKey ? "••••••••••••• (saved)" : "sk-ant-..."}
              className="flex-1 bg-white/[0.06] text-white/60 text-xs rounded-lg px-3 py-2 outline-none border border-white/[0.08] focus:border-white/20"
            />
            <button
              onClick={handleSaveKey}
              disabled={!apiKeyInput}
              className="px-3 py-2 text-xs rounded-lg bg-white/10 text-white/70 hover:bg-white/15 disabled:opacity-30 transition-colors"
            >
              {keySaved ? "Saved ✓" : "Save"}
            </button>
          </div>

          {selectedId && (
            <button
              onClick={handleClassify}
              disabled={!hasApiKey || isClassifying}
              className="text-xs py-2 rounded-lg bg-white/[0.06] text-white/50 hover:bg-white/10 hover:text-white/70 disabled:opacity-30 transition-colors"
            >
              {isClassifying
                ? "Classifying…"
                : "✦ Classify selected asset with Claude"}
            </button>
          )}
        </section>
      </div>
    </div>
  );
}

function StatusDot({
  active,
  connected,
}: {
  active: boolean;
  connected: boolean;
}) {
  const color = !active ? "#ffffff20" : connected ? "#22c55e80" : "#f59e0b80";
  const label = !active ? "Stopped" : connected ? "Connected" : "Connecting…";

  return (
    <div className="flex items-center gap-1.5">
      <span className="text-white/30 text-[10px]">{label}</span>
      <span
        className="w-2 h-2 rounded-full"
        style={{
          background: color,
          boxShadow: active && connected ? `0 0 6px ${color}` : "none",
        }}
      />
    </div>
  );
}
