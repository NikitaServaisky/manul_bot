
CREATE TABLE IF NOT EXISTS work_schedule (
    id SERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    
    shift_date DATE NOT NULL,
    
    -- Precise hours for the garage operation
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    
    -- Role for this specific shift (if an employee changes roles, e.g., 'diagnostics', 'reception')
    assigned_role VARCHAR(100), 
    
    notes TEXT,                                   -- Special instructions from the manager
    is_published BOOLEAN DEFAULT FALSE,           -- Visible to employee only when published
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT unique_user_date_schedule UNIQUE (user_id, shift_date)
);