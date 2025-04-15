-- Database Functions
-- This file contains all custom PostgreSQL functions for the Declutter application

-- Function to list all tables in the public schema
CREATE OR REPLACE FUNCTION get_tables()
RETURNS TABLE (table_name text) AS $$
BEGIN
    RETURN QUERY
    SELECT table_name::text
    FROM information_schema.tables
    WHERE table_schema = 'public'
    ORDER BY table_name;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER; 