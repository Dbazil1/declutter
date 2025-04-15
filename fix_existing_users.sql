-- Fix missing emails in public.users
UPDATE public.users 
SET email = auth.users.email 
FROM auth.users 
WHERE public.users.id = auth.users.id AND (public.users.email IS NULL OR public.users.email = '');

-- Fix missing names in public.users (use raw_user_meta_data if available, otherwise use email as fallback)
UPDATE public.users 
SET 
  first_name = COALESCE(
    (SELECT raw_user_meta_data->>'first_name' FROM auth.users WHERE id = public.users.id),
    (SELECT raw_user_meta_data->'user_metadata'->>'first_name' FROM auth.users WHERE id = public.users.id),
    split_part(email, '@', 1)
  )
WHERE first_name IS NULL OR first_name = '';

UPDATE public.users 
SET 
  last_name = COALESCE(
    (SELECT raw_user_meta_data->>'last_name' FROM auth.users WHERE id = public.users.id),
    (SELECT raw_user_meta_data->'user_metadata'->>'last_name' FROM auth.users WHERE id = public.users.id),
    ''
  )
WHERE last_name IS NULL OR last_name = '';

-- Create missing public.users records for any auth.users without corresponding records
INSERT INTO public.users (id, email, first_name, last_name, role)
SELECT 
  au.id,
  au.email,
  COALESCE(au.raw_user_meta_data->>'first_name', au.raw_user_meta_data->'user_metadata'->>'first_name', split_part(au.email::TEXT, '@', 1)),
  COALESCE(au.raw_user_meta_data->>'last_name', au.raw_user_meta_data->'user_metadata'->>'last_name', ''),
  'user'
FROM auth.users au
LEFT JOIN public.users pu ON au.id = pu.id
WHERE pu.id IS NULL; 