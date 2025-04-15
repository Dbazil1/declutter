-- Re-enable Row Level Security on all tables
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.items ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.item_images ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.public_links ENABLE ROW LEVEL SECURITY;

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

-- Drop existing policies for public_links table
DROP POLICY IF EXISTS "Users can view their own public links" ON public.public_links;
DROP POLICY IF EXISTS "Users can insert their own public links" ON public.public_links;
DROP POLICY IF EXISTS "Users can update their own public links" ON public.public_links;
DROP POLICY IF EXISTS "Users can delete their own public links" ON public.public_links;
DROP POLICY IF EXISTS "Public can view active links" ON public.public_links;

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

-- Create policies for public_links table
CREATE POLICY "Users can view their own public links" ON public.public_links
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Public can view active links" ON public.public_links
    FOR SELECT USING (is_active = true);
    
CREATE POLICY "Users can insert their own public links" ON public.public_links
    FOR INSERT WITH CHECK (auth.uid() = user_id);
    
CREATE POLICY "Users can update their own public links" ON public.public_links
    FOR UPDATE USING (auth.uid() = user_id);
    
CREATE POLICY "Users can delete their own public links" ON public.public_links
    FOR DELETE USING (auth.uid() = user_id); 