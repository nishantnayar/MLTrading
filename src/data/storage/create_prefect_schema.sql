-- Prefect 3.x Schema Setup for ML Trading System
-- This script creates a dedicated schema for Prefect workflow orchestration
-- Separate from the main application data in the 'public' schema

-- Create dedicated schema for Prefect
CREATE SCHEMA IF NOT EXISTS prefect;

-- Create a dedicated user for Prefect (optional but recommended)
-- Uncomment if you want separate user management
/*
CREATE USER prefect_user WITH ENCRYPTED PASSWORD 'your_secure_password';
GRANT CONNECT ON DATABASE mltrading TO prefect_user;
GRANT USAGE ON SCHEMA prefect TO prefect_user;
GRANT CREATE ON SCHEMA prefect TO prefect_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA prefect TO prefect_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA prefect TO prefect_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA prefect GRANT ALL ON TABLES TO prefect_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA prefect GRANT ALL ON SEQUENCES TO prefect_user;
*/

-- Grant permissions to your existing application user
-- Replace 'your_app_user' with your actual database user
GRANT USAGE ON SCHEMA prefect TO your_app_user;
GRANT CREATE ON SCHEMA prefect TO your_app_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA prefect TO your_app_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA prefect TO your_app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA prefect GRANT ALL ON TABLES TO your_app_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA prefect GRANT ALL ON SEQUENCES TO your_app_user;

-- Set search path to include both schemas (application queries can access both)
-- This allows your application to access Prefect data when needed
ALTER DATABASE mltrading SET search_path = public, prefect;

-- Create indexes for better performance on Prefect tables (will be created by Prefect)
-- These are pre-optimizations for common Prefect queries
-- Note: Prefect will create its own tables, these are additional optimizations

-- Create extension for UUID generation if not exists
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Log schema creation
INSERT INTO public.system_logs (
    level,
    component,
    message,
    metadata,
    created_at
) VALUES (
    'INFO',
    'database_setup',
    'Prefect schema created successfully',
    '{"schema": "prefect", "purpose": "workflow_orchestration"}',
    NOW()
);

COMMENT ON SCHEMA prefect IS 'Dedicated schema for Prefect 3.x workflow orchestration tables';