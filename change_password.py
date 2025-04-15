import os
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

# Initialize Supabase client with service role key
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
)

# First, get the user ID for the email
response = supabase.auth.admin.list_users()
user = next((u for u in response if u.email == "insert user email here"), None)

if user:
    # Update the password
    result = supabase.auth.admin.update_user_by_id(
        user.id,
        {"password": "insert new password here"}
    )
    
    if result.user:
        print("Password updated successfully!")
    else:
        print("Failed to update password:", result.error)
else:
    print("User not found with that email")