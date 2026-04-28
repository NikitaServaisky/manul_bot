-- 4. Table of parts
CREATE TABLE IF NOT EXISTS inventory (
    item_id SERIAL PRIMARY KEY,            -- Unique part ID
    item_name VARCHAR(255) NOT NULL,       -- Part description (e.g., '10W40 Engine Oil')
    category VARCHAR(100),                 -- Category: 'Oils', 'Brakes', 'Filters', etc.
    quantity INTEGER DEFAULT 0,            -- Current stock level
    unit_price DECIMAL(10, 2),             -- Sale price per unit
    last_restock TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP -- Last inventory update
);