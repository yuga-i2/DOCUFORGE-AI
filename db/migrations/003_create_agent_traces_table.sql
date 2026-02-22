CREATE TABLE IF NOT EXISTS agent_traces (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(36) NOT NULL,
    agent_name VARCHAR(100),
    trace_entry TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_traces_session ON agent_traces(session_id);
