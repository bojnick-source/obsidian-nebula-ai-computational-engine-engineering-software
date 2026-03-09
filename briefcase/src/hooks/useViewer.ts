import type { ViewerPlugin } from "../types/viewer";
import type { AssetRecord } from "../types/asset";
import { ImageViewerPlugin } from "../components/viewer/plugins/ImageViewerPlugin";
import { VideoViewerPlugin } from "../components/viewer/plugins/VideoViewerPlugin";
import { PdfViewerPlugin } from "../components/viewer/plugins/PdfViewerPlugin";
import { DocxViewerPlugin } from "../components/viewer/plugins/DocxViewerPlugin";
import { ThreeViewerPlugin } from "../components/viewer/plugins/ThreeViewerPlugin";

// All registered plugins, sorted by priority descending
const PLUGINS: ViewerPlugin[] = [
  ThreeViewerPlugin,
  PdfViewerPlugin,
  DocxViewerPlugin,
  ImageViewerPlugin,
  VideoViewerPlugin,
].sort((a, b) => b.priority - a.priority);

export function resolvePlugin(asset: AssetRecord): ViewerPlugin | null {
  return PLUGINS.find((p) => p.canRender(asset)) ?? null;
}

export function useViewer() {
  return { resolvePlugin, plugins: PLUGINS };
}
