-- Create a storage bucket for item images
INSERT INTO storage.buckets (id, name, public)
VALUES ('item-images', 'item-images', true)
ON CONFLICT (id) DO NOTHING;

-- Set up storage policies
CREATE POLICY "Allow public access to item images"
ON storage.objects FOR SELECT
USING (bucket_id = 'item-images');

CREATE POLICY "Allow authenticated users to upload item images"
ON storage.objects FOR INSERT
WITH CHECK (
    bucket_id = 'item-images' AND
    auth.role() = 'authenticated'
);

CREATE POLICY "Allow users to update their own item images"
ON storage.objects FOR UPDATE
USING (
    bucket_id = 'item-images' AND
    auth.uid()::text = (storage.foldername(name))[1]
);

CREATE POLICY "Allow users to delete their own item images"
ON storage.objects FOR DELETE
USING (
    bucket_id = 'item-images' AND
    auth.uid()::text = (storage.foldername(name))[1]
); 