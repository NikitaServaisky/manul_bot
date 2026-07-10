
CREATE TABLE IF NOT EXISTS vacation_requests (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- Request details
    -- Examples: 'vacation', 'sick_leave', 'unpaid_leave', 'army_reserve'
    request_type VARCHAR(50) NOT NULL, 
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,
    total_days DECIMAL(4,1),                      -- Allows half-days (e.g., 1.5 days)
    user_notes TEXT,                              -- Employee's explanation
    
    -- Connection to your documents table (e.g., for sick leave certificates)
    document_id INT REFERENCES user_documents(id) ON DELETE SET NULL,
    
    -- Workflow status
    -- 0: Pending, 1: Approved, -1: Rejected
    status SMALLINT DEFAULT 0,
    processed_by BIGINT REFERENCES users(user_id), -- Manager who approved/rejected
    admin_notes TEXT,                              -- Manager's response
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);