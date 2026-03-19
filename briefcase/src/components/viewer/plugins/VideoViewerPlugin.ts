import type { ViewerPlugin } from "../../../types/viewer";
import type { AssetRecord } from "../../../types/asset";

// Track all active video elements so dispose() can clean up every instance,
// not just the last one rendered. Using a Set prevents concurrent-preview bugs
// where a second renderPreview() would overwrite a module-level single reference.
const activeVideos = new Set<HTMLVideoElement>();

export const VideoViewerPlugin: ViewerPlugin = {
  id: "video-viewer",
  displayName: "Video Viewer",
  supportedMimeTypes: ["video/mp4", "video/webm", "video/ogg"],
  priority: 10,

  canRender(asset: AssetRecord): boolean {
    return asset.fileType.startsWith("video/");
  },

  async renderPreview(
    container: HTMLElement,
    _asset: AssetRecord,
    objectUrl: string
  ): Promise<void> {
    container.innerHTML = "";
    container.style.display = "flex";
    container.style.alignItems = "center";
    container.style.justifyContent = "center";
    container.style.height = "100%";
    container.style.background = "#000";

    const video = document.createElement("video");
    video.src = objectUrl;
    video.controls = true;
    video.style.maxWidth = "100%";
    video.style.maxHeight = "100%";
    activeVideos.add(video);
    container.appendChild(video);
  },

  async renderThumbnail(_asset: AssetRecord): Promise<Blob> {
    const canvas = document.createElement("canvas");
    canvas.width = 128;
    canvas.height = 96;
    const ctx = canvas.getContext("2d")!;
    ctx.fillStyle = "#0f0f0f";
    ctx.fillRect(0, 0, 128, 96);
    // Play icon
    ctx.fillStyle = "rgba(255,255,255,0.6)";
    ctx.beginPath();
    ctx.moveTo(48, 30);
    ctx.lineTo(48, 66);
    ctx.lineTo(84, 48);
    ctx.closePath();
    ctx.fill();
    return new Promise((resolve, reject) =>
      canvas.toBlob((b) => (b ? resolve(b) : reject(new Error("canvas.toBlob returned null"))), "image/png")
    );
  },

  dispose(): void {
    for (const video of activeVideos) {
      video.pause();
      video.src = "";
    }
    activeVideos.clear();
  },
};
