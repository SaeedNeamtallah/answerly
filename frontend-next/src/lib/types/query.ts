export interface QueryRequestPayload {
  query: string;
  top_k?: number;
  language?: "ar" | "en";
  asset_id?: number;
}

export interface QuerySource {
  document_name: string;
  chunk_index: number;
  similarity: number;
  asset_id?: number | null;
}

export interface QueryResponse {
  answer: string;
  sources?: QuerySource[];
  context_used?: number;
}
