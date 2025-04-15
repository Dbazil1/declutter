import os
import asyncio
import uuid
from dotenv import load_dotenv
from postgrest import AsyncPostgrestClient
from supabase import create_client

async def test_connection():
    # Load environment variables
    load_dotenv()
    
    # Get Supabase credentials
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")
    service_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
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
                result = await postgrest.from_(table).select("*").limit(1).execute()
                print(f"- {table} ({len(result.data)} records)")
            except Exception as e:
                print(f"- {table} (Error: {str(e)})")
        
        # Check permissions on the items table
        if service_key:
            print("\nTesting write permissions on items table...")
            
            # Create a Supabase client with service role key for admin actions
            admin_client = create_client(url, service_key)
            
            # Get a user ID to use for testing
            users = admin_client.table('users').select('id').limit(1).execute()
            if users.data:
                test_user_id = users.data[0]['id']
                
                # Create a test item
                print(f"Creating test item for user {test_user_id}...")
                test_item_id = str(uuid.uuid4())
                
                try:
                    # Try to create a test item
                    response = admin_client.table('items').insert({
                        'id': test_item_id,
                        'user_id': test_user_id,
                        'name': 'Test Item - To Be Deleted',
                        'price_usd': 10,
                        'price_local': 100,
                        'sale_status': 'claimed_not_paid'
                    }).execute()
                    
                    if response.data:
                        print("✅ Successfully created test item!")
                        
                        # Try to update the item
                        update_response = admin_client.table('items').update({
                            'name': 'Test Item - Updated',
                            'price_usd': 20
                        }).eq('id', test_item_id).execute()
                        
                        if update_response.data:
                            print("✅ Successfully updated test item!")
                        else:
                            print("❌ Failed to update test item")
                        
                        # Delete the test item
                        admin_client.table('items').delete().eq('id', test_item_id).execute()
                        print("✅ Successfully deleted test item")
                    else:
                        print("❌ Failed to create test item")
                except Exception as e:
                    print(f"❌ Error during item operations: {str(e)}")
                    if hasattr(e, 'json'):
                        print(f"Error details: {e.json()}")
            else:
                print("No users found for testing")
        else:
            print("\nSkipping write tests - SUPABASE_SERVICE_ROLE_KEY not found")
        
        return True
            
    except Exception as e:
        print(f"❌ Connection failed: {str(e)}")
        if hasattr(e, 'json'):
            print(f"Error details: {e.json()}")
        return False

if __name__ == "__main__":
    asyncio.run(test_connection()) 