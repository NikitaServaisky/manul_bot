-- 1. Users tables (owners, staff)
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,           -- Telegram unique ID (BIGINT for long IDs)
    username VARCHAR(255),                 -- User's Telegram display name
    role VARCHAR(50) DEFAULT 'staff',      -- Access level: 'admin', 'staff', or 'mechanic'
    is_active SMALLINT DEFAULT 1,          -- Status: 1 for active, 0 for disabled
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP -- Registration date
);