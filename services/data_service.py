import streamlit as st
import os
from dotenv import load_dotenv
from postgrest import AsyncPostgrestClient
from supabase import create_client
import traceback
import uuid
import time
import random
import string
from utils.image_utils import generate_and_store_sales_photos
import datetime

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
        key = os.getenv("SUPABASE_KEY")
        
        # Log the configuration (without showing full keys)
        if url:
            masked_url = url[:15] + "..." if len(url) > 15 else url
            st.write(f"Debug: Supabase URL configured: {masked_url}")
        else:
            st.error("Error: SUPABASE_URL environment variable is not set")
            return None
            
        if key:
            masked_key = key[:5] + "..." + key[-5:] if len(key) > 10 else "***"
            st.write(f"Debug: Supabase API key available: {masked_key}")
        else:
            st.error("Error: SUPABASE_KEY environment variable is not set")
            return None
            
        try:
            client = create_client(url, key)
            # Test the connection
            if os.getenv('ENVIRONMENT') == 'development':
                st.write("Attempting to connect to Supabase...")
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

# Initialize Supabase PostgREST client for data operations
async def init_postgrest():
    if 'postgrest_client' not in st.session_state:
        # For data operations, we use the service role key
        service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        st.session_state.postgrest_client = AsyncPostgrestClient(
            base_url=f"{os.getenv('SUPABASE_URL')}/rest/v1",
            headers={
                "apikey": service_key,
                "Authorization": f"Bearer {service_key}"
            }
        )

# Load items from database
@st.cache_data(ttl=60)
def load_items(force_reload=False):
    if force_reload:
        st.cache_data.clear()
    try:
        # Get items with their images and sales images in a single query
        response = st.session_state.supabase.table('items')\
            .select('*, item_images(image_url, sales_image_overlay_url, sales_image_extended_url)')\
            .eq('user_id', st.session_state.user.id)\
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
        # First create the item
        response = st.session_state.supabase.table('items')\
            .insert(item_data)\
            .execute()
        
        if not response.data:
            return None
            
        item = response.data[0]
        
        # If there's an image, upload it
        if image:
            # Generate a unique filename
            file_extension = image.name.split('.')[-1]
            filename = f"{item['id']}/{uuid.uuid4()}.{file_extension}"
            
            # Upload the image to Supabase Storage
            storage_response = st.session_state.supabase.storage\
                .from_('item-images')\
                .upload(filename, image.getvalue(), {
                    'content-type': f'image/{file_extension}'
                })
            
            # Get the public URL of the uploaded image
            image_url = st.session_state.supabase.storage\
                .from_('item-images')\
                .get_public_url(filename)
            
            # Add the image reference to the item_images table
            st.session_state.supabase.table('item_images')\
                .insert({
                    'item_id': item['id'],
                    'image_url': image_url,
                    'is_primary': True
                })\
                .execute()
            
            # Generate and store sales photos
            generate_and_store_sales_photos(
                st.session_state.supabase,
                item['id'], 
                image_url, 
                item_data['price_usd'], 
                item_data['price_local'], 
                item_data['name']
            )
            
            # Update the item with the image URL
            item['image_url'] = image_url
            
        return item
    except Exception as e:
        st.error(f"Error adding item: {str(e)}")
        st.error(traceback.format_exc())
        return None

# Update item
def update_item(item_id, item_data, image=None):
    try:
        # Get the current item data to check for changes
        current_item = st.session_state.supabase.table('items')\
            .select('*, item_images(image_url)')\
            .eq('id', item_id)\
            .execute()
        
        if not current_item.data:
            return None
            
        current_item = current_item.data[0]
        
        # Update the item
        response = st.session_state.supabase.table('items')\
            .update(item_data)\
            .eq('id', item_id)\
            .execute()
        
        if not response.data:
            return None
            
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
            # Generate a unique filename
            file_extension = image.name.split('.')[-1]
            filename = f"{item['id']}/{uuid.uuid4()}.{file_extension}"
            
            # Upload the image to Supabase Storage
            storage_response = st.session_state.supabase.storage\
                .from_('item-images')\
                .upload(filename, image.getvalue(), {
                    'content-type': f'image/{file_extension}',
                    'cache-control': 'no-cache'
                })
            
            # Get the public URL of the uploaded image
            image_url = st.session_state.supabase.storage\
                .from_('item-images')\
                .get_public_url(filename)
            
            # Update or add the image reference in item_images table
            st.session_state.supabase.table('item_images')\
                .upsert({
                    'item_id': item['id'],
                    'image_url': image_url,
                    'is_primary': True
                })\
                .execute()
            
            # Update the item with the image URL
            item['image_url'] = image_url
        else:
            # Use existing image URL
            item['image_url'] = current_item['item_images'][0]['image_url'] if current_item.get('item_images') else None
        
        # Generate and store sales photos if needed
        if should_regenerate and item['image_url']:
            # Clear any existing sales photos
            try:
                # List all files for this item
                files = st.session_state.supabase.storage\
                    .from_('item-images')\
                    .list(str(item['id']))
                
                # Delete sales photos
                for file in files:
                    if 'sales_' in file['name']:
                        st.session_state.supabase.storage\
                            .from_('item-images')\
                            .remove([f"{item['id']}/{file['name']}"])
            except:
                pass  # Ignore errors in cleanup
            
            # Generate new photos
            generate_and_store_sales_photos(
                st.session_state.supabase,
                item['id'],
                item['image_url'],
                item_data['price_usd'],
                item_data['price_local'],
                item_data['name']
            )
        
        # Clear all caches
        st.cache_data.clear()
        
        return item
    except Exception as e:
        st.error(f"Error updating item: {str(e)}")
        st.error(traceback.format_exc())
        return None 

# Generate a unique code for public links
def generate_link_code(length=10):
    characters = string.ascii_letters + string.digits
    while True:
        # Generate a random code
        code = ''.join(random.choice(characters) for _ in range(length))
        
        # Check if this code already exists
        response = st.session_state.supabase.table('public_links')\
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
        
        # Create the public link record
        response = st.session_state.supabase.table('public_links')\
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
        response = st.session_state.supabase.table('public_links')\
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
        response = st.session_state.supabase.table('public_links')\
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
        response = st.session_state.supabase.table('public_links')\
            .delete()\
            .eq('id', link_id)\
            .eq('user_id', st.session_state.user.id)\
            .execute()
            
        if response.data:
            return True
        return False
    except Exception as e:
        st.error(f"Error deleting public link: {str(e)}")
        return False

# Get public link by code (no authentication required)
def get_public_link_by_code(link_code):
    try:
        response = st.session_state.supabase.table('public_links')\
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

# Load available items for a public link
def load_public_items(user_id):
    try:
        # Get available items with their images
        response = st.session_state.supabase.table('items')\
            .select('*, item_images(image_url)')\
            .eq('user_id', user_id)\
            .eq('is_sold', False)\
            .execute()
            
        # Process the response to include image URLs and filter for available items
        items = []
        for item in response.data:
            # Skip items that are explicitly unavailable
            if item.get('status') == 'unavailable':
                continue
                
            # Get the first image URL if available
            image_url = None
            if 'item_images' in item and item['item_images']:
                image_url = item['item_images'][0]['image_url']
            
            # Add image URL to the item
            item['image_url'] = image_url
            items.append(item)
            
        return items
    except Exception as e:
        st.error(f"Error loading public items: {str(e)}")
        return [] 

# Update user's WhatsApp information
def update_user_whatsapp(phone_number, share_for_items=False):
    try:
        # Format phone number to standard E.164 format
        # This is a basic cleaning, not a full validation
        cleaned_phone = ''.join(c for c in phone_number if c.isdigit() or c == '+')
        
        # Update user's WhatsApp info in database
        response = st.session_state.supabase.table('users')\
            .update({
                'whatsapp_phone': cleaned_phone,
                'share_whatsapp_for_items': share_for_items
            })\
            .eq('id', st.session_state.user.id)\
            .execute()
            
        return bool(response.data)
    except Exception as e:
        st.error(f"Error updating WhatsApp information: {str(e)}")
        return False

# Get user's WhatsApp information
def get_user_whatsapp_info(user_id):
    try:
        response = st.session_state.supabase.table('users')\
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
        response = st.session_state.supabase.table('users')\
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
        
        if os.getenv('ENVIRONMENT') == 'development':
            st.write(f"Service role query returned: {response.data}")
            
        return response.data
    except Exception as e:
        st.error(f"Service role query error: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None

# Get user details safely, trying multiple methods
def get_user_details_safely(user_id):
    """Get user details using multiple fallback methods"""
    try:
        # First, try with regular client
        response = st.session_state.supabase.table('users').select('*').eq('id', user_id).execute()
        
        if response and hasattr(response, 'data') and response.data:
            return response.data[0]
            
        # If that fails, try with service role
        service_data = check_user_details(user_id)
        if service_data and len(service_data) > 0:
            return service_data[0]
            
        # If still no data, return None
        return None
    except Exception as e:
        if os.getenv('ENVIRONMENT') == 'development':
            st.error(f"Error getting user details safely: {str(e)}")
            import traceback
            st.error(traceback.format_exc())
        return None 