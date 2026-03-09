import type { ViewerPlugin } from "../../../types/viewer";
import type { AssetRecord } from "../../../types/asset";

export const ImageViewerPlugin: ViewerPlugin = {
  id: "image-viewer",
  displayName: "Image Viewer",
  supportedMimeTypes: [
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
    "image/svg+xml",
    "image/tiff",
    "image/bmp",
    "image/avif",
  ],
  priority: 10,

  canRender(asset: AssetRecord): boolean {
    return asset.fileType.startsWith("image/");
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
    container.style.background = "#0f0f0f";

    const img = document.createElement("img");
    img.src = objectUrl;
    img.style.maxWidth = "100%";
    img.style.maxHeight = "100%";
    img.style.objectFit = "contain";
    img.alt = "Preview";
    container.appendChild(img);
  },

  async renderThumbnail(asset: AssetRecord): Promise<Blob> {
    // Placeholder 1x1 transparent PNG for thumbnails not yet generated
    void asset;
    const canvas = document.createElement("canvas");
    canvas.width = 128;
    canvas.height = 96;
    const ctx = canvas.getContext("2d")!;
    ctx.fillStyle = "#1a1a1a";
    ctx.fillRect(0, 0, 128, 96);
    return new Promise((resolve) => canvas.toBlob((b) => resolve(b!), "image/png"));
  },

  dispose(): void {
    // Nothing to clean up
  },
};
