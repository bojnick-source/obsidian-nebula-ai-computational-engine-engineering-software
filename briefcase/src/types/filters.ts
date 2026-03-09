import type {
  Audience,
  Confidentiality,
  Importance,
  VettedStatus,
} from "./asset";

export interface AssetFilter {
  project?: string;
  importance?: Importance;
  audience?: Audience;
  confidentiality?: Confidentiality;
  vettedStatus?: VettedStatus;
  fileType?: string;
  tag?: string;
  limit?: number;
  offset?: number;
}

export interface AssetPatch {
  title?: string;
  project?: string;
  subproject?: string;
  importance?: Importance;
  audience?: Audience;
  confidentiality?: Confidentiality;
  vettedStatus?: VettedStatus;
  tags?: string[];
  classificationExplanation?: string;
  supersededBy?: string;
}
