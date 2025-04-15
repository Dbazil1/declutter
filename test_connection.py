import os
import asyncio
from dotenv import load_dotenv
from postgrest import AsyncPostgrestClient

async def test_connection():
    # Load environment variables
    load_dotenv()
    
    # Get Supabase credentials
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    
    if not url or not key:
        print("Error: SUPABASE_URL or SUPABASE_KEY not found in .env file")
        return False
    
    try:
        # Initialize Supabase client
        print("Attempting to connect to Supabase...")
        
        # Create REST URL
        rest_url = f"{url}/rest/v1"
        
        # Initialize Postgrest client
        postgrest = AsyncPostgrestClient(
            base_url=rest_url,
            headers={
                "apikey": key,
                "Authorization": f"Bearer {key}"
            }
        )
        
        # Test connection with a simple query
        print("Testing database connection...")
        response = await postgrest.from_("users").select("*").execute()
        
        print("✅ Successfully connected to Supabase!")
        
        # List all tables in the database by trying to query them
        print("\nListing all tables in the database:")
        tables = ['users', 'items', 'item_images']
        for table in tables:
            try:
                await postgrest.from_(table).select("*").limit(1).execute()
                print(f"- {table}")
            except Exception:
                print(f"- {table} (empty or doesn't exist)")
        
        return True
            
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection()) 