CREATE TABLE IF NOT EXISTS documents (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    filename VARCHAR(255),
    format VARCHAR(20),
    char_count INTEGER,
    ingested_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_documents_session ON documents(session_id);
