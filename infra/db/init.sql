-- Kích hoạt extension pgvector và kiểm tra phiên bản
CREATE EXTENSION IF NOT EXISTS vector;
SELECT extname, extversion FROM pg_extension WHERE extname = 'vector';
