-- 02_expand_users_table.sql

-- Identification and contact details
ALTER TABLE users ADD COLUMN IF NOT EXISTS phone_number VARCHAR(500);
ALTER TABLE users ADD COLUMN IF NOT EXISTS email VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS id_number VARCHAR(500);
ALTER TABLE users ADD COLUMN IF NOT EXISTS address TEXT;
ALTER TABLE users ADD COLUMN IF NOT EXISTS birth_date DATE;
ALTER TABLE users ADD COLUMN IF NOT EXISTS start_date DATE DEFAULT CURRENT_DATE; -- Employment start date

-- Salary settings and employment standards
-- Salary type: 'hourly', 'daily', or 'monthly' (global)
ALTER TABLE users ADD COLUMN IF NOT EXISTS salary_type VARCHAR(500) DEFAULT 'hourly';
ALTER TABLE users ADD COLUMN IF NOT EXISTS base_salary_rate VARCHAR(500) DEFAULT 0.00; -- Rate (per hour/day/month)
ALTER TABLE users ADD COLUMN IF NOT EXISTS travel_allowance DECIMAL(10, 2) DEFAULT 0.00; -- Daily travel reimbursement
ALTER TABLE users ADD COLUMN IF NOT EXISTS pension_start_date DATE; -- Date for starting pension contributions

-- Bank details for salary transfers
ALTER TABLE users ADD COLUMN IF NOT EXISTS bank_name VARCHAR(500);
ALTER TABLE users ADD COLUMN IF NOT EXISTS bank_branch VARCHAR(500);
ALTER TABLE users ADD COLUMN IF NOT EXISTS bank_account_number VARCHAR(500);

-- Status and administrative management
ALTER TABLE users ADD COLUMN IF NOT EXISTS emergency_contact_name VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS emergency_contact_phone VARCHAR(20);
ALTER TABLE users ADD COLUMN IF NOT EXISTS notes TEXT; -- Administrative notes
ALTER TABLE users ADD COLUMN IF NOT EXISTS employment_status VARCHAR(50) DEFAULT 'active'; -- e.g., active, on_leave, terminated