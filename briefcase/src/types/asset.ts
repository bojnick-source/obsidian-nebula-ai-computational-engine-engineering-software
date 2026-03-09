export type Importance =
  | "critical"
  | "executive"
  | "technical"
  | "research"
  | "approved"
  | "archived";

export type Audience =
  | "executive"
  | "engineering"
  | "client"
  | "internal"
  | "public";

export type Confidentiality = "confidential" | "internal" | "unrestricted";

export type VettedStatus =
  | "unvetted"
  | "ai-vetted"
  | "peer-reviewed"
  | "human-approved"
  | "final-locked";

export type RelationshipType =
  | "derived-from"
  | "supersedes"
  | "presented-in"
  | "reviewed-by"
  | "rendered-from"
  | "exported-as"
  | "bundles"
  | "references";

export interface AssetRecord {
  id: string;
  contentHash: string;
  title: string;
  fileType: string;
  originalName: string;
  project: string | null;
  subproject: string | null;
  sourceAgent: string | null;
  pipelineId: string | null;
  importance: Importance;
  audience: Audience;
  confidentiality: Confidentiality;
  vettedStatus: VettedStatus;
  tags: string[];
  classificationConfidence: number;
  classificationExplanation: string;
  createdAt: string;
  ingestedAt: string;
  version: number;
  supersededBy: string | null;
}

export interface AssetRelationship {
  sourceId: string;
  targetId: string;
  relationshipType: RelationshipType;
  createdAt: string;
}

// UI grouping helper
export interface DrawerGroup {
  key: string;
  label: string;
  importance?: Importance;
  assetIds: string[];
  isOpen: boolean;
}
