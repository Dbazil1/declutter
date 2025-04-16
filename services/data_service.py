import streamlit as st
import os
from dotenv import load_dotenv
from supabase import create_client
import traceback
import uuid
import time
import random
import string
from utils.image_utils import generate_and_store_sales_photos
import datetime
from utils.translation_utils import t
from auth_state import get_user_id

# Set development mode flag
is_development = os.getenv('ENVIRONMENT', '').lower() == 'development'

# Load environment variables
load_dotenv()

# Debug function to print environment variables (without exposing sensitive data)
def debug_env():
    st.write("Environment Variables:")
    st.write(f"SUPABASE_URL: {'Set' if os.getenv('SUPABASE_URL') else 'Not Set'}")
    st.write(f"SUPABASE_KEY: {'Set' if os.getenv('SUPABASE_KEY') else 'Not Set'}")
    st.write(f"SUPABASE_SERVICE_ROLE_KEY: {'Set' if os.getenv('SUPABASE_SERVICE_ROLE_KEY') else 'Not Set'}")

# Initialize Supabase client
def init_supabase():
    try:
        url = os.getenv("SUPABASE_URL")
        # Use service role key instead of regular key for all operations
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        
        # Only show debug info in development mode
        if is_development:
            # Log the configuration (without showing full keys)
            if url:
                masked_url = url[:15] + "..." if len(url) > 15 else url
                st.write(f"Debug: Supabase URL configured: {masked_url}")
            else:
                st.error("Error: SUPABASE_URL environment variable is not set")
                return None
                
            if key:
                masked_key = key[:5] + "..." + key[-5:] if len(key) > 10 else "***"
                st.write(f"Debug: Supabase SERVICE ROLE key available: {masked_key}")
            else:
                st.error("Error: SUPABASE_SERVICE_ROLE_KEY environment variable is not set")
                return None
        else:
            # In production, just check if variables exist
            if not url or not key:
                st.error("Error: Required environment variables are not set")
                return None
            
        try:
            client = create_client(url, key)
            # Test the connection
            if is_development:
                st.write("Attempting to connect to Supabase with SERVICE ROLE key...")
                # Simple query to test connection
                try:
                    test = client.table('users').select('count', count='exact').execute()
                    st.write(f"Connection successful! Found {test.count if hasattr(test, 'count') else 'unknown'} users.")
                except Exception as test_err:
                    st.warning(f"Connection established but test query failed: {str(test_err)}")
                    
            return client
        except Exception as client_err:
            st.error(f"Failed to initialize Supabase client: {str(client_err)}")
            st.error(traceback.format_exc())
            return None
    except Exception as e:
        st.error(f"Error initializing Supabase client: {str(e)}")
        st.error(traceback.format_exc())
        return None

# Initialize PostgreSQL client
def init_postgrest():
    """
    Stub function to maintain API compatibility.
    The app now uses the synchronous Supabase client instead.
    """
    pass

# Load items from database
@st.cache_data(ttl=60)
def load_items(force_reload=False):
    if force_reload:
        st.cache_data.clear()
    try:
        user_id = get_user_id()
        if not user_id:
            return []
        
        # Use service role key for database operations
        service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        url = os.getenv("SUPABASE_URL")
        service_client = create_client(url, service_key)
        
        # Get items with their images and sales images in a single query
        response = service_client.table('items')\
            .select('*, item_images(image_url, sales_image_overlay_url, sales_image_extended_url)')\
            .eq('user_id', user_id)\
            .execute()
            
        # Process the response to include image URLs
        items = []
        for item in response.data:
            # Get the first image URL if available
            image_url = None
            sales_overlay_url = None
            sales_extended_url = None
            if 'item_images' in item and item['item_images']:
                image_url = item['item_images'][0]['image_url']
                sales_overlay_url = item['item_images'][0].get('sales_image_overlay_url')
                sales_extended_url = item['item_images'][0].get('sales_image_extended_url')
            
            # Add all URLs to the item
            item['image_url'] = image_url
            item['sales_overlay_url'] = sales_overlay_url
            item['sales_extended_url'] = sales_extended_url
            items.append(item)
            
        return items
    except Exception as e:
        st.error(f"Error loading items: {str(e)}")
        st.error(traceback.format_exc())
        return []

# Add new item
def add_item(item_data, image=None):
    try:
        # Check if user is authenticated
        if not st.session_state.get('user'):
            st.error("User not authenticated")
            return None
        
        # Always use service role key for item operations
        service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        url = os.getenv("SUPABASE_URL")
        service_client = create_client(url, service_key)
        
        # Insert the item using service role
        try:
            response = service_client.table('items')\
                .insert(item_data)\
                .execute()
                
            if not response.data:
                st.error("Failed to create item")
                return None
        except Exception as insert_error:
            st.error(f"Error adding item: {str(insert_error)}")
            if is_development:
                st.error(traceback.format_exc())
            return None
            
        item = response.data[0]
        
        # If there's an image, upload it
        if image:
            try:
                # Generate a unique filename
                file_extension = image.name.split('.')[-1]
                filename = f"{item['id']}/{uuid.uuid4()}.{file_extension}"
                
                # Upload the image to Supabase Storage
                storage_response = service_client.storage\
                    .from_('item-images')\
                    .upload(filename, image.getvalue(), {
                        'content-type': f'image/{file_extension}'
                    })
                
                # Get the public URL of the uploaded image
                image_url = service_client.storage\
                    .from_('item-images')\
                    .get_public_url(filename)
                
                # Add the image reference to the item_images table
                service_client.table('item_images')\
                    .insert({
                        'item_id': item['id'],
                        'image_url': image_url,
                        'is_primary': True
                    })\
                    .execute()
                
                # Generate and store sales photos
                try:
                    generate_and_store_sales_photos(
                        service_client,
                        item['id'], 
                        image_url, 
                        item_data['price_usd'], 
                        item_data['price_local'], 
                        item_data['name']
                    )
                except Exception as sales_error:
                    # Non-critical error, log but continue
                    if is_development:
                        st.warning(f"Error generating sales photos: {str(sales_error)}")
                        st.warning(traceback.format_exc())
            except Exception as storage_error:
                # Log the storage error but continue
                if is_development:
                    st.warning(f"Error uploading image: {str(storage_error)}")
                    st.warning(traceback.format_exc())
        
        return item
    except Exception as e:
        st.error(f"Error in add_item: {str(e)}")
        if is_development:
            st.error(traceback.format_exc())
        return None

# Update an existing item
def update_item(item_id, item_data, image=None):
    try:
        # Always use service role key for item operations
        service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        url = os.getenv("SUPABASE_URL")
        service_client = create_client(url, service_key)
        
        # Check if item exists and belongs to user
        current_item = service_client.table('items')\
            .select('*, item_images(*)')\
            .eq('id', item_id)\
            .execute()
        
        if not current_item.data:
            st.error(f"Error: Could not find item with ID {item_id}")
            return None
            
        current_item = current_item.data[0]
        
        # Update the item using service role
        try:
            response = service_client.table('items')\
                .update(item_data)\
                .eq('id', item_id)\
                .execute()
                
            if not response.data:
                st.error("Error: Item update failed")
                return None
        except Exception as update_error:
            st.error(f"Error updating item: {str(update_error)}")
            if is_development:
                st.error(traceback.format_exc())
            return None
        
        # Get the updated item data
        item = response.data[0]
        
        # Check if we need to regenerate photos
        should_regenerate = (
            image is not None or  # New image uploaded
            item_data.get('name') != current_item.get('name') or  # Name changed
            item_data.get('price_usd') != current_item.get('price_usd') or  # USD price changed
            item_data.get('price_local') != current_item.get('price_local')  # Local price changed
        )
        
        # If there's a new image, upload it
        if image:
            try:
                # Generate a unique filename
                file_extension = image.name.split('.')[-1]
                filename = f"{item['id']}/{uuid.uuid4()}.{file_extension}"
                
                # Upload the image to Supabase Storage
                storage_response = service_client.storage\
                    .from_('item-images')\
                    .upload(filename, image.getvalue(), {
                        'content-type': f'image/{file_extension}',
                        'cache-control': 'no-cache'
                    })
                
                # Get the public URL of the uploaded image
                image_url = service_client.storage\
                    .from_('item-images')\
                    .get_public_url(filename)
                
                # Update or add the image reference in item_images table
                service_client.table('item_images')\
                    .upsert({
                        'item_id': item['id'],
                        'image_url': image_url,
                        'is_primary': True
                    })\
                    .execute()
                
                # Update the item with the image URL
                item['image_url'] = image_url
            except Exception as image_error:
                st.error(f"Error uploading image: {str(image_error)}")
                if is_development:
                    st.error(traceback.format_exc())
                # Continue with the update, even if image upload failed
        else:
            # Use existing image URL if available
            if current_item.get('item_images') and len(current_item['item_images']) > 0:
                item['image_url'] = current_item['item_images'][0]['image_url']
            else:
                item['image_url'] = None
        
        # Generate and store sales photos if needed
        if should_regenerate and item['image_url']:
            try:
                # Clear any existing sales photos
                try:
                    # List all files for this item
                    files = service_client.storage\
                        .from_('item-images')\
                        .list(str(item['id']))
                    
                    # Delete sales photos
                    for file in files:
                        if 'sales_' in file['name']:
                            service_client.storage\
                                .from_('item-images')\
                                .remove([f"{item['id']}/{file['name']}"])
                except:
                    pass  # Ignore errors in cleanup
                
                # Generate new photos
                generate_and_store_sales_photos(
                    service_client,
                    item['id'],
                    item['image_url'],
                    item_data['price_usd'],
                    item_data['price_local'],
                    item_data['name']
                )
            except Exception as photo_error:
                st.error(f"Error handling sales photos: {str(photo_error)}")
                if is_development:
                    st.error(traceback.format_exc())
        
        # Clear all caches to ensure fresh data
        st.cache_data.clear()
        
        return item
    except Exception as e:
        st.error(f"Error updating item: {str(e)}")
        st.error(traceback.format_exc())
        return None

# Generate a unique code for public links
def generate_link_code(length=10):
    characters = string.ascii_letters + string.digits
    
    # Use service role key for database operations
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    url = os.getenv("SUPABASE_URL")
    service_client = create_client(url, service_key)
    
    while True:
        # Generate a random code
        code = ''.join(random.choice(characters) for _ in range(length))
        
        # Check if this code already exists
        response = service_client.table('public_links')\
            .select('id')\
            .eq('link_code', code)\
            .execute()
            
        # If no results, this code is unique
        if not response.data:
            return code

# Create a new public link
def create_public_link(name="My Items Collection"):
    try:
        link_code = generate_link_code()
        
        # Use service role key for database operations
        service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        url = os.getenv("SUPABASE_URL")
        service_client = create_client(url, service_key)
        
        # Create the public link record
        response = service_client.table('public_links')\
            .insert({
                'user_id': st.session_state.user.id,
                'link_code': link_code,
                'name': name,
                'is_active': True
            })\
            .execute()
            
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Error creating public link: {str(e)}")
        st.error(traceback.format_exc())
        return None

# Get all public links for the current user
def get_user_public_links():
    try:
        # Use service role key for database operations
        service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        url = os.getenv("SUPABASE_URL")
        service_client = create_client(url, service_key)
        
        response = service_client.table('public_links')\
            .select('*')\
            .eq('user_id', st.session_state.user.id)\
            .execute()
            
        return response.data
    except Exception as e:
        st.error(f"Error fetching public links: {str(e)}")
        return []

# Update a public link
def update_public_link(link_id, data):
    try:
        # Use service role key for database operations
        service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        url = os.getenv("SUPABASE_URL")
        service_client = create_client(url, service_key)
        
        response = service_client.table('public_links')\
            .update(data)\
            .eq('id', link_id)\
            .eq('user_id', st.session_state.user.id)\
            .execute()
            
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Error updating public link: {str(e)}")
        return None

# Delete a public link
def delete_public_link(link_id):
    try:
        # Use service role key for database operations
        service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        url = os.getenv("SUPABASE_URL")
        service_client = create_client(url, service_key)
        
        response = service_client.table('public_links')\
            .delete()\
            .eq('id', link_id)\
            .eq('user_id', st.session_state.user.id)\
            .execute()
            
        return True
    except Exception as e:
        st.error(f"Error deleting public link: {str(e)}")
        return False

# Get a public link by its code
def get_public_link_by_code(link_code):
    try:
        # Use service role key for database operations
        service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        url = os.getenv("SUPABASE_URL")
        service_client = create_client(url, service_key)
        
        response = service_client.table('public_links')\
            .select('*')\
            .eq('link_code', link_code)\
            .eq('is_active', True)\
            .execute()
            
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Error fetching public link: {str(e)}")
        return None

# Load items for a public link
def load_public_items(user_id):
    try:
        # Use service role key for database operations
        service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        url = os.getenv("SUPABASE_URL")
        service_client = create_client(url, service_key)
        
        response = service_client.table('items')\
            .select('*, item_images(image_url)')\
            .eq('user_id', user_id)\
            .eq('is_sold', False)\
            .execute()
            
        # Process the response to include image URLs
        items = []
        for item in response.data:
            # Get the first image URL if available
            image_url = None
            if 'item_images' in item and item['item_images']:
                image_url = item['item_images'][0]['image_url']
            
            # Add the image URL to the item
            item['image_url'] = image_url
            items.append(item)
            
        return items
    except Exception as e:
        st.error(f"Error loading public items: {str(e)}")
        return []

# Update user's WhatsApp information
def update_user_whatsapp(phone_number, share_for_items=False):
    try:
        # Use service role key for database operations
        service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        url = os.getenv("SUPABASE_URL")
        service_client = create_client(url, service_key)
        
        response = service_client.table('users')\
            .update({
                'whatsapp_phone': phone_number,
                'share_whatsapp_for_items': share_for_items
            })\
            .eq('id', st.session_state.user.id)\
            .execute()
            
        return bool(response.data)
    except Exception as e:
        st.error(f"Error updating WhatsApp info: {str(e)}")
        return False

# Get user's WhatsApp information
def get_user_whatsapp_info(user_id):
    try:
        # Use service role key for database operations
        service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        url = os.getenv("SUPABASE_URL")
        service_client = create_client(url, service_key)
        
        response = service_client.table('users')\
            .select('whatsapp_phone, share_whatsapp_for_items')\
            .eq('id', user_id)\
            .execute()
            
        if response.data:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Error getting WhatsApp info: {str(e)}")
        return None

# Update user's WhatsApp sharing preferences
def update_whatsapp_sharing(share_for_items):
    try:
        # Use service role key for database operations
        service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        url = os.getenv("SUPABASE_URL")
        service_client = create_client(url, service_key)
        
        response = service_client.table('users')\
            .update({
                'share_whatsapp_for_items': share_for_items
            })\
            .eq('id', st.session_state.user.id)\
            .execute()
            
        return bool(response.data)
    except Exception as e:
        st.error(f"Error updating WhatsApp sharing preferences: {str(e)}")
        return False

# Check user details using service role (bypasses RLS)
def check_user_details(user_id):
    """Debug function to check user details using service role key to bypass RLS"""
    try:
        # Create a new client with service role key
        service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        url = os.getenv("SUPABASE_URL")
        client = create_client(url, service_key)
        
        # Try to get user details
        response = client.table('users').select('*').eq('id', user_id).execute()
        
        if is_development:
            st.write(f"Service role query returned: {response.data}")
            
        return response.data
    except Exception as e:
        st.error(f"Service role query error: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None

# Get user details safely, trying multiple methods
def get_user_details_safely(user_id):
    """Safely get user details from the database with multiple fallback methods."""
    try:
        if is_development:
            st.write(f"Debug: Attempting to get user details for ID: {user_id}")
        
        # Try with service role first
        service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        url = os.getenv("SUPABASE_URL")
        client = create_client(url, service_key)
        
        response = client.table('users').select('*').eq('id', user_id).execute()
        
        if response.data and len(response.data) > 0:
            if is_development:
                st.write(f"Debug: Successfully retrieved user details with service role")
            return response.data[0]
        
        # If that fails, try with the current user's token
        if st.session_state.get('supabase'):
            response = st.session_state.supabase.table('users').select('*').eq('id', user_id).execute()
            
            if response.data and len(response.data) > 0:
                if is_development:
                    st.write(f"Debug: Successfully retrieved user details with user token")
                return response.data[0]
        
        if is_development:
            st.write("Debug: Failed to retrieve user details with both methods")
        return None
        
    except Exception as e:
        if is_development:
            st.error(f"Error getting user details: {str(e)}")
            st.error(traceback.format_exc())
        return None 