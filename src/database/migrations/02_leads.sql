-- 2. Leads tabel (scan results)
CREATE TABLE IF NOT EXISTS leads (
    id SERIAL PRIMARY KEY,                 -- Internal auto-incremented ID
    post_content TEXT,                     -- Full text of the Facebook post
    post_url TEXT UNIQUE,                  -- Unique URL to prevent processing the same post twice
    status VARCHAR(20) DEFAULT 'new',      -- Workflow status: 'new', 'contacted', 'closed', 'rejected'
    assigned_to BIGINT,                    -- Reference to the user (staff) handling this lead
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Discovery time
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, -- Last status update
    CONSTRAINT fk_user FOREIGN KEY(assigned_to) REFERENCES users(user_id) -- Link to users table
);

-- 3. Leads rabel seens previus
CREATE TABLE IF NOT EXISTS seen_leads (
    url TEXT PRIMARY KEY,                  -- The post URL (already analyzed by AI)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP -- Timestamp of analysis
);