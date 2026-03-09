export interface Collection {
  id: string;
  name: string;
  description: string;
  coverAssetId: string | null;
  createdAt: string;
  updatedAt: string;
  itemCount: number;
}

export interface CollectionItem {
  collectionId: string;
  assetId: string;
  position: number;
  slideNotes: string;
}
