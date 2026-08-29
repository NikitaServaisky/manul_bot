-- 03_user_documents.sql

CREATE TABLE IF NOT EXISTS user_documents (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Document classification
    -- Examples: 'sick_leave', 'bl_250', 'id_copy', 'license', 'insurance', 'contract'
    doc_type VARCHAR(50) NOT NULL, 
    
    -- File metadata and storage
    -- Path or URL to the file stored on your server/Immich
    file_path TEXT NOT NULL,
    file_name VARCHAR(255),
    file_size_kb INTEGER,
    
    -- Critical dates
    issue_date DATE,               -- The date the document was issued
    expiry_date DATE,              -- Important for insurance or medical permits
    upload_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Workflow and status
    -- 0: Pending, 1: Processed/Approved, -1: Rejected
    status SMALLINT DEFAULT 0,
    processed_by BIGINT REFERENCES users(user_id), -- Admin who reviewed the doc
    admin_notes TEXT,                              -- Feedback from HR or accounting
    
    -- Metadata for external systems
    morning_sync_status BOOLEAN DEFAULT FALSE,     -- Track if synced with Morning API
    external_ref_id VARCHAR(100)                   -- ID from Morning or other external system
);