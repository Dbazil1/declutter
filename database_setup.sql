-- UUID Extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Auth Schema and Types
CREATE SCHEMA IF NOT EXISTS auth;

-- Users Table
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY REFERENCES auth.users(id),
    email TEXT,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    language_preference TEXT NOT NULL DEFAULT 'en',
    whatsapp_phone TEXT,
    share_whatsapp_for_items BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Items Table
CREATE TABLE IF NOT EXISTS public.items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES auth.users(id),
    name TEXT NOT NULL,
    description TEXT,
    category TEXT,
    condition TEXT,
    price INTEGER,
    price_usd INTEGER,
    price_local INTEGER,
    status TEXT DEFAULT 'available',
    is_sold BOOLEAN DEFAULT false,
    sold_to TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    sale_status TEXT CHECK (sale_status IN ('paid_picked_up', 'paid_pending_pickup', 'claimed_not_paid', NULL))
);

-- Item Images Table
CREATE TABLE IF NOT EXISTS public.item_images (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    item_id UUID REFERENCES public.items(id) ON DELETE CASCADE,
    image_url TEXT NOT NULL,
    sales_image_overlay_url TEXT,
    sales_image_extended_url TEXT,
    is_primary BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW()),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::text, NOW())
);

-- Row Level Security
-- Enable RLS on tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.item_images ENABLE ROW LEVEL SECURITY;

-- Drop existing policies for users table
DROP POLICY IF EXISTS "Users can view their own data" ON public.users;
DROP POLICY IF EXISTS "Users can update their own data" ON public.users;
DROP POLICY IF EXISTS "Users can create their own profile" ON public.users;

-- Drop existing policies for items table
DROP POLICY IF EXISTS "Users can view all items" ON public.items;
DROP POLICY IF EXISTS "Users can insert their own items" ON public.items;
DROP POLICY IF EXISTS "Users can update their own items" ON public.items;
DROP POLICY IF EXISTS "Users can delete their own items" ON public.items;

-- Drop existing policies for item_images table
DROP POLICY IF EXISTS "Users can view all item images" ON public.item_images;
DROP POLICY IF EXISTS "Users can insert images for their items" ON public.item_images;
DROP POLICY IF EXISTS "Users can update images for their items" ON public.item_images;
DROP POLICY IF EXISTS "Users can delete images for their items" ON public.item_images;

-- Create policies for users table
CREATE POLICY "Users can view their own data" ON public.users
    FOR SELECT USING (auth.uid() = id);
    
CREATE POLICY "Users can update their own data" ON public.users
    FOR UPDATE USING (auth.uid() = id);
    
CREATE POLICY "Users can create their own profile" ON public.users
    FOR INSERT WITH CHECK (auth.uid() = id);

-- Create policies for items table
CREATE POLICY "Users can view all items" ON public.items
    FOR SELECT USING (true);
    
CREATE POLICY "Users can insert their own items" ON public.items
    FOR INSERT WITH CHECK (auth.uid() = user_id);
    
CREATE POLICY "Users can update their own items" ON public.items
    FOR UPDATE USING (auth.uid() = user_id);
    
CREATE POLICY "Users can delete their own items" ON public.items
    FOR DELETE USING (auth.uid() = user_id);

-- Create policies for item_images table
CREATE POLICY "Users can view all item images" ON public.item_images
    FOR SELECT USING (true);
    
CREATE POLICY "Users can insert images for their items" ON public.item_images
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.items
            WHERE items.id = item_images.item_id
            AND items.user_id = auth.uid()
        )
    );
    
CREATE POLICY "Users can update images for their items" ON public.item_images
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM public.items
            WHERE items.id = item_images.item_id
            AND items.user_id = auth.uid()
        )
    );
    
CREATE POLICY "Users can delete images for their items" ON public.item_images
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM public.items
            WHERE items.id = item_images.item_id
            AND items.user_id = auth.uid()
        )
    );

-- Add new columns if they don't exist
DO $$ 
BEGIN
    -- Add is_sold column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'items' AND column_name = 'is_sold') THEN
        ALTER TABLE public.items ADD COLUMN is_sold BOOLEAN DEFAULT false;
    END IF;

    -- Add sold_to column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'items' AND column_name = 'sold_to') THEN
        ALTER TABLE public.items ADD COLUMN sold_to TEXT;
    END IF;

    -- Add sales image columns if they don't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'item_images' AND column_name = 'sales_image_overlay_url') THEN
        ALTER TABLE public.item_images ADD COLUMN sales_image_overlay_url TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'item_images' AND column_name = 'sales_image_extended_url') THEN
        ALTER TABLE public.item_images ADD COLUMN sales_image_extended_url TEXT;
    END IF;

    -- Add sale_status column if it doesn't exist
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'items' 
        AND column_name = 'sale_status'
    ) THEN
        ALTER TABLE public.items 
        ADD COLUMN sale_status TEXT CHECK (sale_status IN ('paid_picked_up', 'paid_pending_pickup', 'claimed_not_paid', NULL));
    END IF;

    -- Add price_usd and price_local columns if they don't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'items' AND column_name = 'price_usd') THEN
        ALTER TABLE public.items ADD COLUMN price_usd INTEGER;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'items' AND column_name = 'price_local') THEN
        ALTER TABLE public.items ADD COLUMN price_local INTEGER;
    END IF;

    -- Add WhatsApp related columns if they don't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'users' AND column_name = 'whatsapp_phone') THEN
        ALTER TABLE public.users ADD COLUMN whatsapp_phone TEXT;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'users' AND column_name = 'share_whatsapp_for_items') THEN
        ALTER TABLE public.users ADD COLUMN share_whatsapp_for_items BOOLEAN DEFAULT false;
    END IF;

END $$;

-- Create function to handle user creation
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
  first_name_val TEXT;
  last_name_val TEXT;
BEGIN
    -- Try to get first name and last name from different possible metadata locations
    first_name_val := COALESCE(
        NEW.raw_user_meta_data->>'first_name',
        NEW.raw_user_meta_data->'user_metadata'->>'first_name',
        NEW.raw_app_meta_data->>'first_name',
        NEW.email::TEXT
    );
    
    last_name_val := COALESCE(
        NEW.raw_user_meta_data->>'last_name',
        NEW.raw_user_meta_data->'user_metadata'->>'last_name',
        NEW.raw_app_meta_data->>'last_name',
        ''
    );
    
    -- Split email at @ sign if no first name was found
    IF first_name_val = NEW.email::TEXT THEN
        first_name_val := split_part(NEW.email::TEXT, '@', 1);
    END IF;
    
    INSERT INTO public.users (id, email, first_name, last_name, role)
    VALUES (
        NEW.id,
        NEW.email,
        first_name_val,
        last_name_val,
        'user'
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create trigger for new user creation
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create triggers for updated_at
DROP TRIGGER IF EXISTS update_users_updated_at ON public.users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_items_updated_at ON public.items;
CREATE TRIGGER update_items_updated_at
    BEFORE UPDATE ON public.items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_item_images_updated_at ON public.item_images;
CREATE TRIGGER update_item_images_updated_at
    BEFORE UPDATE ON public.item_images
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
