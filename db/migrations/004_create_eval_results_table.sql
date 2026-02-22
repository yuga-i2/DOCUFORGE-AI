CREATE TABLE IF NOT EXISTS eval_results (
    id SERIAL PRIMARY KEY,
    eval_id VARCHAR(20),
    question TEXT,
    expected_answer TEXT,
    actual_answer TEXT,
    accuracy_score FLOAT,
    faithfulness_score FLOAT,
    ran_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_eval_ran_at ON eval_results(ran_at);
