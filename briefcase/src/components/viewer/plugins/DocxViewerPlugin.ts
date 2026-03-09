import type { ViewerPlugin } from "../../../types/viewer";
import type { AssetRecord } from "../../../types/asset";

const DOCX_MIME =
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
const MD_MIME = "text/markdown";
const TEXT_MIMES = ["text/plain", "text/csv", "text/html"];

export const DocxViewerPlugin: ViewerPlugin = {
  id: "docx-viewer",
  displayName: "Document Viewer",
  supportedMimeTypes: [DOCX_MIME, MD_MIME, ...TEXT_MIMES],
  priority: 20,

  canRender(asset: AssetRecord): boolean {
    return (
      asset.fileType === DOCX_MIME ||
      asset.fileType === MD_MIME ||
      asset.fileType.startsWith("text/")
    );
  },

  async renderPreview(
    container: HTMLElement,
    asset: AssetRecord,
    objectUrl: string
  ): Promise<void> {
    container.innerHTML = "";
    container.style.display = "flex";
    container.style.flexDirection = "column";
    container.style.height = "100%";
    container.style.overflow = "hidden";

    const scrollArea = document.createElement("div");
    scrollArea.style.overflow = "auto";
    scrollArea.style.flex = "1";
    scrollArea.style.background = "#1e1e2e";
    scrollArea.style.padding = "24px";
    scrollArea.style.color = "rgba(255,255,255,0.87)";
    scrollArea.style.fontFamily = "Georgia, serif";
    scrollArea.style.lineHeight = "1.7";
    container.appendChild(scrollArea);

    if (asset.fileType === DOCX_MIME) {
      const mammoth = await import("mammoth");
      const resp = await fetch(objectUrl);
      const buf = await resp.arrayBuffer();
      const result = await mammoth.convertToHtml({ arrayBuffer: buf });
      const wrapper = document.createElement("div");
      wrapper.innerHTML = result.value;
      wrapper.style.maxWidth = "740px";
      wrapper.style.margin = "0 auto";
      scrollArea.appendChild(wrapper);
    } else if (asset.fileType === MD_MIME || asset.originalName.endsWith(".md")) {
      const { marked } = await import("marked");
      const resp = await fetch(objectUrl);
      const text = await resp.text();
      const html = await marked(text);
      const wrapper = document.createElement("div");
      wrapper.innerHTML = html;
      wrapper.style.maxWidth = "740px";
      wrapper.style.margin = "0 auto";
      scrollArea.appendChild(wrapper);
    } else {
      // Plain text
      const resp = await fetch(objectUrl);
      const text = await resp.text();
      const pre = document.createElement("pre");
      pre.textContent = text;
      pre.style.fontFamily = "JetBrains Mono, monospace";
      pre.style.fontSize = "13px";
      pre.style.whiteSpace = "pre-wrap";
      pre.style.wordBreak = "break-all";
      scrollArea.appendChild(pre);
    }
  },

  async renderThumbnail(_asset: AssetRecord): Promise<Blob> {
    const canvas = document.createElement("canvas");
    canvas.width = 128;
    canvas.height = 96;
    const ctx = canvas.getContext("2d")!;
    ctx.fillStyle = "#1e2a3a";
    ctx.fillRect(0, 0, 128, 96);
    ctx.fillStyle = "rgba(255,255,255,0.15)";
    [14, 24, 34, 44, 54, 64].forEach((y) => ctx.fillRect(16, y, 96, 2));
    ctx.fillStyle = "rgba(255,255,255,0.4)";
    ctx.font = "bold 9px sans-serif";
    ctx.fillText("DOC", 52, 80);
    return new Promise((resolve) => canvas.toBlob((b) => resolve(b!), "image/png"));
  },

  dispose(): void {},
};
