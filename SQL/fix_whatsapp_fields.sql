-- Make sure WhatsApp fields exist and have proper defaults
DO $$ 
BEGIN
    -- Add whatsapp_phone column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'users' AND column_name = 'whatsapp_phone') THEN
        ALTER TABLE public.users ADD COLUMN whatsapp_phone TEXT;
    END IF;

    -- Add share_whatsapp_for_items column if it doesn't exist
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                  WHERE table_name = 'users' AND column_name = 'share_whatsapp_for_items') THEN
        ALTER TABLE public.users ADD COLUMN share_whatsapp_for_items BOOLEAN DEFAULT false;
    END IF;
END $$;

-- Set default values for any NULL values
UPDATE public.users 
SET share_whatsapp_for_items = false 
WHERE share_whatsapp_for_items IS NULL; 