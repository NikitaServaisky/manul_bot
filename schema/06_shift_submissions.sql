
CREATE TABLE IF NOT EXISTS shift_submissions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    
    -- The specific date the employee is submitting availability for
    shift_date DATE NOT NULL,
    
    -- Examples: 'morning', 'evening', 'full_day', 'unavailable'
    preference VARCHAR(50) DEFAULT 'full_day', 
    
    user_notes TEXT,                              -- E.g., "Can only work until 14:00"
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Prevent duplicate submissions for the same employee on the same day
    CONSTRAINT unique_user_date_submission UNIQUE (user_id, shift_date)
);