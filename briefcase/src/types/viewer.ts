import type { AssetRecord } from "./asset";

export interface ViewerPlugin {
  id: string;
  displayName: string;
  supportedMimeTypes: string[];
  /** Higher priority wins when multiple plugins match. */
  priority: number;
  canRender(asset: AssetRecord): boolean;
  renderPreview(
    container: HTMLElement,
    asset: AssetRecord,
    objectUrl: string
  ): Promise<void>;
  renderThumbnail(asset: AssetRecord): Promise<Blob>;
  dispose(): void;
}
