-- Phase 2A: Supabase pgvector Setup

-- 1. Enable the pgvector extension to work with embedding vectors
CREATE EXTENSION IF NOT EXISTS vector;

-- 2. Create the document_sections table with the correct schema
CREATE TABLE IF NOT EXISTS document_sections (
    id bigserial primary key,
    content text not null,
    -- all-MiniLM-L6-v2 produces 384-dimensional vectors
    embedding vector(384) not null,
    document_name text not null,
    created_at timestamptz default now()
);

-- 3. Create an HNSW index for fast cosine similarity search
-- HNSW (Hierarchical Navigable Small World) is a state-of-the-art algorithm for approximate nearest neighbor search.
-- It builds a multi-layered graph to quickly find the closest vectors.
-- vector_cosine_ops specifies that we want to use cosine distance, which is standard for embeddings from models like sentence-transformers,
-- because cosine similarity measures the angle between vectors (i.e., semantic similarity) regardless of magnitude.
CREATE INDEX ON document_sections USING hnsw (embedding vector_cosine_ops);

-- 4. Create a Postgres function for vector similarity search
-- match_threshold specifies the minimum cosine similarity score (0 to 1) required for a match to be considered relevant.
CREATE OR REPLACE FUNCTION match_document_sections (
  query_embedding vector(384),
  match_threshold float DEFAULT 0.5,
  match_count int DEFAULT 5
)
RETURNS TABLE (
  id bigint,
  content text,
  document_name text,
  similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
  RETURN QUERY
  SELECT
    document_sections.id,
    document_sections.content,
    document_sections.document_name,
    -- Calculate cosine similarity (1 - cosine distance)
    1 - (document_sections.embedding <=> query_embedding) AS similarity
  FROM document_sections
  -- Filter by the threshold
  WHERE 1 - (document_sections.embedding <=> query_embedding) > match_threshold
  -- Order by highest similarity first
  ORDER BY document_sections.embedding <=> query_embedding
  LIMIT match_count;
END;
$$;
