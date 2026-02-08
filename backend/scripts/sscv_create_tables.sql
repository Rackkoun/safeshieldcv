
-- file sscv_create_tables.sql
-- Table structure
DROP TABLE IF EXISTS incident;

CREATE TABLE incident (
    id SERIAL PRIMARY KEY,
    violation_type VARCHAR(100) NOT NULL,
    missing_items TEXT[],
    location VARCHAR(200),
    evidence_images TEXT[], -- array of evidences
    reported_date DATE NOT NULL,
    reported_time TIME NOT NULL,
    report_text TEXT,
    email_recipients TEXT[],
    email_sent BOOLEAN DEFAULT FALSE,
    email_sent_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- permissions on table to user
GRANT ALL PRIVILEGES ON TABLE incident TO sscv_user;
ALTER TABLE incident OWNER TO sscv_user;