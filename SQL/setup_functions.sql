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

-- Create public_links table if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'public_links') THEN
        CREATE TABLE public.public_links (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID REFERENCES auth.users(id),
            link_code VARCHAR(50) UNIQUE NOT NULL,
            name TEXT,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
            updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
        );

        -- Enable Row Level Security
        ALTER TABLE public.public_links ENABLE ROW LEVEL SECURITY;
        
        -- Create policies for public_links table
        CREATE POLICY "Users can view their own public links" ON public.public_links
            FOR SELECT USING (auth.uid() = user_id);
            
        CREATE POLICY "Users can insert their own public links" ON public.public_links
            FOR INSERT WITH CHECK (auth.uid() = user_id);
            
        CREATE POLICY "Users can update their own public links" ON public.public_links
            FOR UPDATE USING (auth.uid() = user_id);
            
        CREATE POLICY "Users can delete their own public links" ON public.public_links
            FOR DELETE USING (auth.uid() = user_id);
        
        -- Create trigger for updated_at
        CREATE TRIGGER update_public_links_updated_at
            BEFORE UPDATE ON public.public_links
            FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    END IF;
END $$; 