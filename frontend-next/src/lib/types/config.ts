export interface ProviderConfigResponse {
  available?: {
    llm?: string[];
    embedding?: string[];
    vector_db?: string[];
  };
  llm_provider?: string;
  embedding_provider?: string;
  vector_db_provider?: string;
  provider_selection_migrated?: boolean;
  provider_selection_updated_fields?: string[];
  retrieval_top_k?: number;
  chunk_strategy?: string;
  chunk_size?: number;
  chunk_overlap?: number;
  parent_chunk_size?: number;
  parent_chunk_overlap?: number;
  retrieval_candidate_k?: number;
  retrieval_hybrid_enabled?: boolean;
  retrieval_hybrid_alpha?: number;
  retrieval_rerank_enabled?: boolean;
  retrieval_rerank_top_k?: number;
  query_rewrite_enabled?: boolean;
  retrieval_hnsw_ef_search?: number;
}

export interface ProviderConfigUpdatePayload {
  llm_provider: string;
  embedding_provider: string;
  vector_db_provider?: string;
  retrieval_top_k?: number;
  chunk_strategy?: string;
  chunk_size?: number;
  chunk_overlap?: number;
  parent_chunk_size?: number;
  parent_chunk_overlap?: number;
  retrieval_candidate_k?: number;
  retrieval_hybrid_enabled?: boolean;
  retrieval_hybrid_alpha?: number;
  retrieval_rerank_enabled?: boolean;
  retrieval_rerank_top_k?: number;
  query_rewrite_enabled?: boolean;
  retrieval_hnsw_ef_search?: number;
}
