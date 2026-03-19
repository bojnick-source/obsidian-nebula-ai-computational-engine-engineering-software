import type { ViewerPlugin } from "../../../types/viewer";
import type { AssetRecord } from "../../../types/asset";

export const PdfViewerPlugin: ViewerPlugin = {
  id: "pdf-viewer",
  displayName: "PDF Viewer",
  supportedMimeTypes: ["application/pdf"],
  priority: 20,

  canRender(asset: AssetRecord): boolean {
    return asset.fileType === "application/pdf";
  },

  async renderPreview(
    container: HTMLElement,
    _asset: AssetRecord,
    objectUrl: string
  ): Promise<void> {
    container.innerHTML = "";
    container.style.display = "flex";
    container.style.flexDirection = "column";
    container.style.height = "100%";
    container.style.overflow = "hidden";

    // Load PDF.js dynamically to avoid upfront bundle cost
    const pdfjsLib = await import("pdfjs-dist");

    // Set worker source — Vite will resolve this from node_modules
    pdfjsLib.GlobalWorkerOptions.workerSrc = new URL(
      "pdfjs-dist/build/pdf.worker.min.mjs",
      import.meta.url
    ).toString();

    const loadingTask = pdfjsLib.getDocument(objectUrl);
    const pdf = await loadingTask.promise;
    const totalPages = pdf.numPages;

    const scrollArea = document.createElement("div");
    scrollArea.style.overflow = "auto";
    scrollArea.style.flex = "1";
    scrollArea.style.background = "#1a1a1a";
    scrollArea.style.padding = "16px";
    container.appendChild(scrollArea);

    for (let pageNum = 1; pageNum <= Math.min(totalPages, 10); pageNum++) {
      const page = await pdf.getPage(pageNum);
      const viewport = page.getViewport({ scale: 1.2 });
      const canvas = document.createElement("canvas");
      canvas.width = viewport.width;
      canvas.height = viewport.height;
      canvas.style.display = "block";
      canvas.style.marginBottom = "12px";
      canvas.style.borderRadius = "4px";
      const ctx = canvas.getContext("2d")!;
      await page.render({ canvasContext: ctx, viewport }).promise;
      scrollArea.appendChild(canvas);
    }

    if (totalPages > 10) {
      const note = document.createElement("p");
      note.textContent = `Showing first 10 of ${totalPages} pages. Open file to view all.`;
      note.style.color = "rgba(255,255,255,0.4)";
      note.style.fontSize = "12px";
      note.style.textAlign = "center";
      scrollArea.appendChild(note);
    }
  },

  async renderThumbnail(_asset: AssetRecord): Promise<Blob> {
    const canvas = document.createElement("canvas");
    canvas.width = 128;
    canvas.height = 96;
    const ctx = canvas.getContext("2d")!;
    ctx.fillStyle = "#2a2a3a";
    ctx.fillRect(0, 0, 128, 96);
    ctx.fillStyle = "rgba(255,255,255,0.15)";
    for (let y = 16; y < 80; y += 10) {
      ctx.fillRect(20, y, 88, 2);
    }
    ctx.fillStyle = "rgba(255,255,255,0.4)";
    ctx.font = "bold 10px sans-serif";
    ctx.fillText("PDF", 54, 52);
    return new Promise((resolve, reject) =>
      canvas.toBlob((b) => (b ? resolve(b) : reject(new Error("canvas.toBlob returned null"))), "image/png")
    );
  },

  dispose(): void {
    // PDF.js cleans up via garbage collection; no explicit teardown needed here
  },
};
