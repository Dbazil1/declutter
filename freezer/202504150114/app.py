import streamlit as st
import os
from dotenv import load_dotenv
from postgrest import AsyncPostgrestClient
from supabase import create_client
import asyncio
from PIL import Image
import io
import traceback
import time
import uuid
import requests
from io import BytesIO
from PIL import ImageDraw, ImageFont
from translations import translations

# Load environment variables
load_dotenv()

# Function to get translated text
def t(key, **kwargs):
    lang = st.session_state.get('language', 'en')
    text = translations[lang].get(key, key)
    return text.format(**kwargs) if kwargs else text

# Function to generate sales photos
def generate_sales_photo(image_url, price_usd, price_local, item_name, style="overlay", item_id=None):
    try:
        # Check cache first if item_id is provided
        if item_id:
            cached_photo = get_cached_sales_photo(item_id, style)
            if cached_photo:
                return cached_photo

        # Download the image
        response = requests.get(image_url)
        if response.status_code != 200:
            return None
            
        # Open the image and convert to RGB if needed
        img = Image.open(BytesIO(response.content))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize large images for better performance
        max_size = 1200
        if img.width > max_size or img.height > max_size:
            ratio = min(max_size/img.width, max_size/img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Create a drawing context
        draw = ImageDraw.Draw(img)
        
        # Calculate font sizes based on image width
        title_size_percent = 0.045  # 4.5% of image width
        price_size_percent = 0.06   # 6% of image width
        title_font_size = int(img.width * title_size_percent)
        price_font_size = int(img.width * price_size_percent)
        
        # Try to load a font
        try:
            # Try different font paths
            font_paths = [
                "/System/Library/Fonts/Arial.ttf",  # macOS
                "/usr/share/fonts/truetype/arial.ttf",  # Linux
                "C:\\Windows\\Fonts\\arial.ttf"  # Windows
            ]
            title_font = None
            price_font = None
            
            for path in font_paths:
                try:
                    title_font = ImageFont.truetype(path, title_font_size)
                    price_font = ImageFont.truetype(path, price_font_size)
                    break
                except:
                    continue
            
            if not title_font or not price_font:
                raise Exception("No suitable font found")
                
        except:
            # Use default font if no system font is available
            title_font = ImageFont.load_default()
            price_font = ImageFont.load_default()
        
        # Format price text
        if price_usd and price_local:
            price_text = f"${price_usd} USD / {price_local} Moneda Local"
        elif price_usd:
            price_text = f"${price_usd} USD"
        elif price_local:
            price_text = f"{price_local} Moneda Local"
        else:
            price_text = ""  # No prices available
        
        if style == "extended":
            # Create a new image with extra space at the bottom
            extension_height = int(img.height * 0.25)  # 25% of original height
            new_img = Image.new('RGB', (img.width, img.height + extension_height), (255, 255, 255))
            new_img.paste(img, (0, 0))
            
            # Create a new drawing context for the extended image
            draw = ImageDraw.Draw(new_img)
            
            # Calculate text dimensions
            title_bbox = draw.textbbox((0, 0), item_name, font=title_font)
            price_bbox = draw.textbbox((0, 0), price_text, font=price_font)
            
            # Center the text in the extended space
            title_x = (img.width - (title_bbox[2] - title_bbox[0])) // 2
            price_x = (img.width - (price_bbox[2] - price_bbox[0])) // 2
            
            # Position text in the extended space with better spacing
            title_y = img.height + (extension_height * 0.25)  # 25% into the extension
            price_y = img.height + (extension_height * 0.65)  # 65% into the extension
            
            # Add the text
            draw.text((title_x, title_y), item_name, fill=(0, 0, 0), font=title_font)
            draw.text((price_x, price_y), price_text, fill=(0, 0, 0), font=price_font)
            
            # Use the new image
            img = new_img
            
        else:  # overlay style
            # Calculate text dimensions
            title_bbox = draw.textbbox((0, 0), item_name, font=title_font)
            price_bbox = draw.textbbox((0, 0), price_text, font=price_font)
            
            # Calculate positions (bottom center with padding)
            title_x = (img.width - (title_bbox[2] - title_bbox[0])) // 2
            price_x = (img.width - (price_bbox[2] - price_bbox[0])) // 2
            
            # Position text with padding from bottom
            title_y = int(img.height * 0.85) - (title_bbox[3] - title_bbox[1])
            price_y = int(img.height * 0.95) - (price_bbox[3] - price_bbox[1])
            
            # Add semi-transparent background for text
            background_height = int(img.height * 0.2)  # 20% of image height
            background = Image.new('RGBA', (img.width, background_height), (0, 0, 0, 128))
            img.paste(background, (0, img.height - background_height), background)
            
            # Create a new drawing context after pasting the background
            draw = ImageDraw.Draw(img)
            
            # Add the text
            draw.text((title_x, title_y), item_name, fill=(255, 255, 255), font=title_font)
            draw.text((price_x, price_y), price_text, fill=(255, 255, 255), font=price_font)
        
        # Save with slightly reduced quality for better performance
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=85)
        img_byte_arr = img_byte_arr.getvalue()
        
        # Cache the result if item_id is provided
        if item_id:
            cache_sales_photo(item_id, img_byte_arr, style)
        
        return img_byte_arr
    except Exception as e:
        st.error(f"Error generating sales photo: {str(e)}")
        st.error(traceback.format_exc())
        return None

# Debug function to print environment variables (without exposing sensitive data)
def debug_env():
    st.write("Environment Variables:")
    st.write(f"SUPABASE_URL: {'Set' if os.getenv('SUPABASE_URL') else 'Not Set'}")
    st.write(f"SUPABASE_SERVICE_ROLE_KEY: {'Set' if os.getenv('SUPABASE_SERVICE_ROLE_KEY') else 'Not Set'}")

# Initialize Supabase client
def init_supabase():
    try:
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Use service role key for auth
        
        if not url or not key:
            st.error("Missing Supabase credentials. Please check your .env file.")
            debug_env()
            return None
            
        return create_client(url, key)
    except Exception as e:
        st.error(f"Error initializing Supabase client: {str(e)}")
        st.error(traceback.format_exc())
        return None

# Initialize Supabase PostgREST client for data operations
async def init_postgrest():
    if 'postgrest_client' not in st.session_state:
        st.session_state.postgrest_client = AsyncPostgrestClient(
            base_url=f"{os.getenv('SUPABASE_URL')}/rest/v1",
            headers={
                "apikey": os.getenv('SUPABASE_SERVICE_ROLE_KEY'),  # Use service role key
                "Authorization": f"Bearer {os.getenv('SUPABASE_SERVICE_ROLE_KEY')}"  # Use service role key
            }
        )

# Set page config
st.set_page_config(
    page_title="Declutter",
    page_icon="🏠",
    layout="wide"
)

# Add custom CSS to make sidebar thinner and fit content
st.markdown("""
    <style>
        [data-testid="stSidebar"] {
            min-width: 250px;
            max-width: 250px;
            background-color: white;
        }
        [data-testid="stSidebar"] > div {
            display: flex;
            flex-direction: column;
            height: 100vh;
            background-color: white;
        }
        [data-testid="stSidebar"] h1 {
            text-align: center;
            font-size: 0.9rem !important;
            margin-top: 0.5rem;
            margin-bottom: 0.5rem;
            font-weight: normal !important;
        }
        [data-testid="stSidebar"] > div > div:first-child {
            margin-top: 0;
        }
        [data-testid="stSidebar"] > div > div:last-child {
            margin-top: auto;
        }
        [data-testid="stSidebar"] .stButton button {
            margin: 0.2rem 0;
        }
        [data-testid="stSidebar"] hr {
            display: none;
        }
        .compact-form {
            background-color: #f8f9fa;
            padding: 1.5rem;
            border-radius: 0.5rem;
            margin: -1rem -1rem 1rem -1rem;
        }
        .compact-form [data-testid="stForm"] {
            background-color: transparent;
            border: none;
            padding: 0;
        }
        .compact-form .stTextInput > div > div {
            padding-bottom: 0.5rem;
        }
        .compact-form .stNumberInput > div > div {
            padding-bottom: 0.5rem;
        }
        .compact-form .stRadio > div {
            gap: 1rem;
            margin-top: 0.5rem;
            margin-bottom: 0.5rem;
        }
        .compact-form .stRadio [data-testid="stMarkdownContainer"] {
            margin: 0;
        }
        .compact-form .stButton button {
            padding: 0.25rem 1rem;
            min-height: 0;
        }
        .compact-form .row {
            display: flex;
            gap: 1rem;
            margin-bottom: 0.5rem;
        }
        .compact-form .row > div {
            flex: 1;
        }
        .status-tag {
            padding: 6px 12px;
            border-radius: 4px;
            font-size: 0.875rem;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            margin-top: 4px;
            margin-right: 4px;
            white-space: nowrap;
            height: 32px;
            line-height: 1;
        }
        .edit-button {
            background-color: #E0E0E0 !important;
            color: #333 !important;
            padding: 4px 8px !important;
            border-radius: 4px !important;
            font-size: 0.875rem !important;
            font-weight: 500 !important;
            height: auto !important;
            margin: 4px 0 !important;
            min-height: 0 !important;
            white-space: nowrap !important;
        }
        .tag-container {
            display: flex;
            align-items: center;
            gap: 8px;
            margin-top: 4px;
        }
        .status-available {
            background-color: #F29F05;
            color: white;
        }
        .status-paid {
            background-color: #048ABF;
            color: white;
        }
        .status-claimed {
            background-color: #A63C94;
            color: white;
        }
        .status-complete {
            background-color: #66B794;
            color: white;
        }
        .status-sold-to {
            background-color: #E0E0E0;
            color: #333333;
        }
        .greeting {
            font-size: 2.5rem;
            font-weight: 600;
            margin-bottom: 2rem;
            color: black;
        }
        /* Center content under photos */
        [data-testid="stImage"] + div {
            text-align: center;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        [data-testid="stImage"] + div > * {
            margin: 0.5rem 0;
        }
        .language-selector {
            position: absolute;
            top: 10px;
            right: 10px;
            z-index: 1000;
        }
        /* Login page styles */
        .login-container {
            max-width: 400px;
            margin: 2rem auto;
            padding: 2rem;
            text-align: center;
        }
        .login-tagline {
            font-size: 2.5rem;
            font-weight: 600;
            text-align: center;
            margin-bottom: 2rem;
            color: #333;
            line-height: 1.2;
        }
        .login-tabs {
            margin-bottom: 2rem;
        }
        .stTextInput > div > div {
            background: white;
        }
        .stTextInput > div > div:focus-within {
            border-color: #333;
            box-shadow: 0 0 0 1px #333;
        }
        .stButton > button {
            width: 100%;
            background-color: #E0E0E0;
            color: #333;
            padding: 0.5rem;
            border: none;
            border-radius: 4px;
            margin-top: 1rem;
            transition: background-color 0.2s ease;
        }
        .stButton > button:hover {
            background-color: #D0D0D0;
        }
        [data-testid="stForm"] {
            background-color: #f8f9fa;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        /* Style for the edit button to match tags */
        [data-testid="baseButton-secondary"] {
            background-color: white !important;
            border: 1px solid #333 !important;
            color: #333 !important;
            padding: 6px 12px !important;
            border-radius: 4px !important;
            font-size: 0.875rem !important;
            font-weight: 500 !important;
            height: 32px !important;
            margin: 4px 0 !important;
            min-height: 0 !important;
            white-space: nowrap !important;
            line-height: 1 !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            box-shadow: none !important;
        }
        [data-testid="baseButton-secondary"]:hover {
            background-color: #f8f9fa !important;
            border-color: #000 !important;
        }
        /* Consistent styling for all buttons */
        button {
            white-space: nowrap !important;
        }
        /* Language selector styling */
        [data-testid="stSelectbox"] {
            margin-bottom: 1rem;
        }
        [data-testid="stSelectbox"] > div > div {
            background-color: white;
            border: 1px solid #ddd;
            padding: 0.25rem;
            cursor: pointer;
            border-radius: 4px;
        }
        [data-testid="stSelectbox"] > div > div:hover {
            border-color: #333;
        }
    </style>
    """, unsafe_allow_html=True)

# Initialize session state
if 'supabase' not in st.session_state:
    st.session_state.supabase = init_supabase()

if 'user' not in st.session_state:
    st.session_state.user = None

if 'postgrest_client' not in st.session_state:
    asyncio.run(init_postgrest())

if 'current_page' not in st.session_state:
    st.session_state.current_page = 'available'

# Initialize language
if 'language' not in st.session_state:
    st.session_state.language = 'en'

# Authentication functions
def login(email: str, password: str):
    try:
        if not email or not password:
            st.error("Please enter both email and password")
            return False
            
        st.write("Attempting to sign in...")
        auth = st.session_state.supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        st.session_state.user = auth.user
        
        # Clear all cached data when logging in
        st.cache_data.clear()
        
        st.success("Login successful!")
        return True
    except Exception as e:
        st.error(f"Login failed: {str(e)}")
        st.error(traceback.format_exc())
        return False

def signup(email: str, password: str, first_name: str, last_name: str):
    try:
        if not email or not password or not first_name or not last_name:
            st.error(t('enter_names'))
            return False
            
        # Validate email format
        if "@" not in email or "." not in email:
            st.error("Please enter a valid email address")
            return False
            
        # Validate password strength
        if len(password) < 8:
            st.error("Password must be at least 8 characters long")
            return False
            
        st.write("Attempting to sign up...")
        auth = st.session_state.supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if auth.user:
            # Create the user record in our users table with name fields
            st.session_state.supabase.table('users').insert({
                'id': auth.user.id,
                'email': auth.user.email,
                'first_name': first_name,
                'last_name': last_name,
                'role': 'user'
            }).execute()
            
        return True
    except Exception as e:
        st.error(f"Signup failed: {str(e)}")
        st.error(traceback.format_exc())
        return False

def logout():
    try:
        st.session_state.supabase.auth.sign_out()
        st.session_state.user = None
        st.success("Logged out successfully!")
    except Exception as e:
        st.error(f"Error during logout: {str(e)}")
        st.error(traceback.format_exc())

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

# Cache generated sales photos in session state
def get_cached_sales_photo(item_id, style="overlay"):
    cache_key = f"sales_photo_{item_id}_{style}"
    return st.session_state.get(cache_key)

def cache_sales_photo(item_id, photo_bytes, style="overlay"):
    cache_key = f"sales_photo_{item_id}_{style}"
    st.session_state[cache_key] = photo_bytes

# Function to generate and store sales photos
def generate_and_store_sales_photos(item_id, image_url, price_usd, price_local, item_name):
    try:
        # Generate both styles of sales photos
        overlay_photo = generate_sales_photo(image_url, price_usd, price_local, item_name, "overlay", item_id)
        extended_photo = generate_sales_photo(image_url, price_usd, price_local, item_name, "extended", item_id)
        
        if overlay_photo and extended_photo:
            # Generate unique filenames with timestamp to prevent caching
            timestamp = int(time.time())
            overlay_filename = f"{item_id}/sales_overlay_{timestamp}.jpg"
            extended_filename = f"{item_id}/sales_extended_{timestamp}.jpg"
            
            # Upload overlay version
            st.session_state.supabase.storage\
                .from_('item-images')\
                .upload(overlay_filename, overlay_photo, {
                    'content-type': 'image/jpeg',
                    'cache-control': 'no-cache'
                })
            
            # Upload extended version
            st.session_state.supabase.storage\
                .from_('item-images')\
                .upload(extended_filename, extended_photo, {
                    'content-type': 'image/jpeg',
                    'cache-control': 'no-cache'
                })
            
            # Get public URLs
            overlay_url = st.session_state.supabase.storage\
                .from_('item-images')\
                .get_public_url(overlay_filename)
            
            extended_url = st.session_state.supabase.storage\
                .from_('item-images')\
                .get_public_url(extended_filename)
            
            # Update the item_images table with the new URLs
            st.session_state.supabase.table('item_images')\
                .update({
                    'sales_image_overlay_url': overlay_url,
                    'sales_image_extended_url': extended_url
                })\
                .eq('item_id', item_id)\
                .execute()
            
            # Clear all caches
            st.cache_data.clear()
            
            return True
    except Exception as e:
        st.error(f"Error generating sales photos: {str(e)}")
        st.error(traceback.format_exc())
    return False

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
            generate_and_store_sales_photos(item['id'], image_url, item_data['price_usd'], item_data['price_local'], item_data['name'])
            
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

# Authentication UI
if st.session_state.user is None:
    # Center the content using columns
    left_col, center_col, right_col = st.columns([1, 2, 1])
    
    with center_col:
        # Create columns for logo centering
        logo_left, logo_center, logo_right = st.columns([1, 2, 1])
        with logo_center:
            # Add logo with fixed size
            st.image("declutter-logo.png", width=250)
        
        # Add tagline
        st.markdown('<h1 class="login-tagline">Are you ready to declutter?</h1>', unsafe_allow_html=True)
        
        # Login/Signup tabs
        tab1, tab2 = st.tabs([t('login'), t('signup')])
        
        with tab1:  # Login tab
            with st.form("login_form"):
                # Pre-fill email if coming from successful signup
                default_email = st.session_state.get('last_signup_email', '')
                email = st.text_input(t('email'), value=default_email, key='login_email')
                password = st.text_input(t('password'), type="password")
                submit = st.form_submit_button(t('login'))
                
                if submit:
                    if login(email, password):
                        # Clear the last signup email after successful login
                        if 'last_signup_email' in st.session_state:
                            del st.session_state.last_signup_email
                        st.rerun()
        
        with tab2:  # Signup tab
            # Show success message above the form if exists
            if 'signup_success' in st.session_state:
                st.success(t('signup_success'))
                st.info(t('proceed_to_login'))
                del st.session_state.signup_success

            with st.form("signup_form"):
                col1, col2 = st.columns(2)
                with col1:
                    first_name = st.text_input(t('first_name'))
                with col2:
                    last_name = st.text_input(t('last_name'))
                new_email = st.text_input(t('email'))
                new_password = st.text_input(t('password'), type="password")
                confirm_password = st.text_input(t('confirm_password'), type="password")
                submit = st.form_submit_button(t('signup'))
                
                if submit:
                    if new_password != confirm_password:
                        st.error(t('passwords_match'))
                    elif not first_name or not last_name:
                        st.error(t('enter_names'))
                    else:
                        with st.spinner(t('creating_account')):
                            if signup(new_email, new_password, first_name, last_name):
                                # Store success state and email
                                st.session_state.signup_success = True
                                st.session_state.last_signup_email = new_email
                                st.rerun()
        
        # Add language selector after the forms
        st.markdown("---")  # Add a divider
        selected_lang = st.selectbox(
            "🌐 Language / Idioma",
            options=[('English', 'en'), ('Español', 'es')],
            format_func=lambda x: x[0],
            key='login_language_selector',
            index=0 if st.session_state.language == 'en' else 1
        )
        if selected_lang[1] != st.session_state.language:
            st.session_state.language = selected_lang[1]

else:
    # Main App UI
    # Get user's first name from the database
    user_info = st.session_state.supabase.table('users')\
        .select('first_name')\
        .eq('id', st.session_state.user.id)\
        .execute()
    
    first_name = user_info.data[0]['first_name'] if user_info.data else t('user')
    
    st.sidebar.image("declutter-logo.png", use_column_width=True)
    
    # Define the navigation options
    nav_options = {
        "📋 " + t('all_items'): "all",
        "🏷️ " + t('available'): "available",
        "💰 " + t('paid_ready'): "paid_ready",
        "⏳ " + t('claimed'): "claimed",
        "✅ " + t('complete'): "complete",
        "👤 " + t('sold_to'): "sold_to",
        "➕ " + t('add_item'): "add",
        "📸 " + t('generate_photos'): "photos"
    }

    # Create buttons for each option
    for label, key in nav_options.items():
        if st.sidebar.button(label, key=f"nav_{key}", use_container_width=True):
            st.session_state.current_page = key
            st.rerun()

    if st.sidebar.button(t('logout')):
        logout()
        st.rerun()

    # Add bazil-dot-studio logo at the very bottom
    st.sidebar.image("bazil-dot-studio.png", use_column_width=True)

    # Add language selector at the very bottom
    st.sidebar.markdown("---")  # Add a divider
    selected_lang = st.sidebar.selectbox(
        "Language / Idioma",
        options=[('English', 'en'), ('Español', 'es')],
        format_func=lambda x: x[0],
        key='language_selector',
        index=0 if st.session_state.language == 'en' else 1
    )
    if selected_lang[1] != st.session_state.language:
        st.session_state.language = selected_lang[1]

    # Main content
    if st.session_state.current_page in ['all', 'available', 'paid_ready', 'claimed', 'complete', 'sold_to']:
        # Set the appropriate title and filter
        show_all = False  # Initialize show_all
        filter_status = None  # Initialize filter_status
        
        if st.session_state.current_page == 'all':
            st.title(t('all_items'))
            filter_status = None
            show_all = True
        elif st.session_state.current_page == 'available':
            st.markdown(f'<p class="greeting">{t("greeting", name=first_name)}</p>', unsafe_allow_html=True)
            st.title(t('available'))
            filter_status = None
            show_all = False
        elif st.session_state.current_page == 'paid_ready':
            st.title(t('paid_ready'))
            filter_status = 'paid_pending_pickup'
            show_all = False
        elif st.session_state.current_page == 'claimed':
            st.title(t('claimed'))
            filter_status = 'claimed_not_paid'
            show_all = False
        elif st.session_state.current_page == 'complete':
            st.title(t('complete'))
            filter_status = 'paid_picked_up'
            show_all = False
        elif st.session_state.current_page == 'sold_to':
            st.title(t('sold_to'))
            filter_status = None
            show_all = False

        # Edit Modal at the top (only shown when editing)
        if st.session_state.get('show_edit_modal') and st.session_state.get('editing_item'):
            with st.form("edit_item_form"):
                item = st.session_state.editing_item
                
                # Wrap the entire form in the compact-form class
                st.markdown('<div class="compact-form">', unsafe_allow_html=True)
                
                # Name field
                name = st.text_input(t('item_name'), value=item['name'])
                
                # Price fields in a row
                col1, col2 = st.columns(2)
                with col1:
                    price_usd = st.number_input("USD", min_value=0, value=int(item.get('price_usd', 0) or 0))
                with col2:
                    price_local = st.number_input("LOCAL", min_value=0, value=int(item.get('price_local', 0) or 0))
                
                # Status and sold_to in a row
                col1, col2 = st.columns([3, 2])
                with col1:
                    status_options = {
                        'available': ('🏷️ ' + t('status_available'), 'status-available'),
                        'paid_pending_pickup': ('💰 ' + t('status_paid'), 'status-paid'),
                        'claimed_not_paid': ('⏳ ' + t('status_claimed'), 'status-claimed'),
                        'paid_picked_up': ('✅ ' + t('status_complete'), 'status-complete')
                    }
                    
                    current_status = item.get('sale_status')
                    selected_status = current_status if current_status in status_options else 'available'
                    
                    status_display = {text: key for key, (text, _) in status_options.items()}
                    selected_status_text = next(text for key, (text, _) in status_options.items() if key == selected_status)
                    
                    new_status_text = st.radio(
                        "Status",
                        options=list(status_display.keys()),
                        index=list(status_display.keys()).index(selected_status_text),
                        horizontal=True,
                        label_visibility="collapsed"
                    )
                    selected_status = status_display[new_status_text]
                
                with col2:
                    sold_to = ""
                    if selected_status != 'available':
                        sold_to = st.text_input("Sold to", value=item.get('sold_to', ''), label_visibility="collapsed", placeholder="Sold to")
                
                # Optional image upload
                image = st.file_uploader(t('upload_new_image'), type=["jpg", "jpeg", "png"])
                
                # Add buttons in a row at the bottom
                col1, col2 = st.columns([1, 1])
                with col1:
                    submit = st.form_submit_button(t('save_changes'))
                    if submit:
                        item_data = {
                            "name": name,
                            "price_usd": int(price_usd) if price_usd > 0 else None,
                            "price_local": int(price_local) if price_local > 0 else None,
                            "sale_status": selected_status,
                            "is_sold": selected_status == 'paid_picked_up'
                        }
                        if selected_status != 'available' and sold_to:
                            item_data['sold_to'] = sold_to
                        updated_item = update_item(item['id'], item_data, image)
                        if updated_item:
                            st.success(t('item_updated'))
                            st.session_state.show_edit_modal = False
                            st.session_state.editing_item = None
                            # Clear the cache to force reload of items
                            st.cache_data.clear()
                            st.rerun()
                with col2:
                    if st.form_submit_button(t('cancel')):
                        st.session_state.show_edit_modal = False
                        st.session_state.editing_item = None
                        st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)

        # Load items
        items = load_items()
        
        # Filter items based on status
        filtered_items = []  # Initialize filtered_items
        if show_all:
            filtered_items = items  # Show all items
        elif filter_status is None:
            if st.session_state.current_page == 'sold_to':
                # Group items by sold_to
                sold_items = [item for item in items if item.get('sold_to')]
                if sold_items:
                    # Group by sold_to
                    sold_to_groups = {}
                    for item in sold_items:
                        buyer = item.get('sold_to', 'Unknown')
                        if buyer not in sold_to_groups:
                            sold_to_groups[buyer] = []
                        sold_to_groups[buyer].append(item)
                    
                    # Display each group
                    for buyer, buyer_items in sold_to_groups.items():
                        st.subheader(f"👤 {buyer}")
                        # Create a grid layout for items
                        cols = st.columns(3)
                        for i, item in enumerate(buyer_items):
                            with cols[i % 3]:
                                if item.get('image_url'):
                                    st.image(item['image_url'], caption=item['name'])
                                else:
                                    st.image("https://via.placeholder.com/200x200?text=No+Image", caption=item['name'])
                                
                                st.write(f"${item['price']:.2f}")
                                st.write(item['name'])
                                
                                # Show status with color coding
                                status_info = {
                                    'paid_pending_pickup': ('💰 ' + t('status_paid'), 'status-paid'),
                                    'claimed_not_paid': ('⏳ ' + t('status_claimed'), 'status-claimed'),
                                    'paid_picked_up': ('✅ ' + t('status_complete'), 'status-complete'),
                                    None: ('🏷️ ' + t('status_available'), 'status-available')
                                }
                                
                                status_text, status_class = status_info.get(item.get('sale_status'), ('🏷️ ' + t('status_available'), 'status-available'))
                                
                                # Create a row for status, sold-to, and edit button
                                st.markdown('<div class="tag-container">', unsafe_allow_html=True)
                                # Adjusted column widths to give more space to the edit button
                                col1, col2, col3 = st.columns([1.5, 1.5, 1])
                                with col1:
                                    st.markdown(f'<div class="status-tag {status_class}">{status_text}</div>', unsafe_allow_html=True)
                                
                                with col2:
                                    # Show sold to name if status is not available
                                    if item.get('sale_status') != 'available' and item.get('sold_to'):
                                        st.markdown(f'<div class="status-tag status-sold-to">👤 {item["sold_to"]}</div>', unsafe_allow_html=True)
                                
                                with col3:
                                    if st.button(t('edit'), key=f"edit_{item['id']}", type="secondary", use_container_width=True):
                                        st.session_state.editing_item = item
                                        st.session_state.show_edit_modal = True
                                        st.rerun()
                                st.markdown('</div>', unsafe_allow_html=True)
                else:
                    st.info(t('no_sold_items'))
            else:
                filtered_items = [item for item in items if not item.get('is_sold')]
        else:
            filtered_items = [item for item in items if item.get('sale_status') == filter_status]
        
        # Display filtered items if not in sold_to view
        if st.session_state.current_page != 'sold_to' and filtered_items:
            # Create a grid layout for items
            cols = st.columns(3)
            for i, item in enumerate(filtered_items):
                with cols[i % 3]:
                    if item.get('image_url'):
                        # Try to use pre-generated sales photo URL
                        if item.get('sales_overlay_url'):
                            st.image(item['sales_overlay_url'], caption=item['name'])
                        else:
                            # Generate and cache if needed
                            sales_photo = generate_sales_photo(
                                item['image_url'],
                                item.get('price_usd'),
                                item.get('price_local'),
                                item['name'],
                                "overlay",
                                item['id']
                            )
                            if sales_photo:
                                st.image(BytesIO(sales_photo), caption=item['name'])
                    else:
                        st.image("https://via.placeholder.com/200x200?text=No+Image", caption=item['name'])
                    
                    # Show prices
                    if item.get('price_usd') and item.get('price_local'):
                        st.write(f"${item['price_usd']} USD / {item['price_local']} Moneda Local")
                    elif item.get('price_usd'):
                        st.write(f"${item['price_usd']} USD")
                    elif item.get('price_local'):
                        st.write(f"{item['price_local']} Moneda Local")
                    
                    # Show status with color coding
                    status_info = {
                        'paid_pending_pickup': ('💰 ' + t('status_paid'), 'status-paid'),
                        'claimed_not_paid': ('⏳ ' + t('status_claimed'), 'status-claimed'),
                        'paid_picked_up': ('✅ ' + t('status_complete'), 'status-complete'),
                        None: ('🏷️ ' + t('status_available'), 'status-available')
                    }
                    
                    status_text, status_class = status_info.get(item.get('sale_status'), ('🏷️ ' + t('status_available'), 'status-available'))
                    
                    # Create a row for status, sold-to, and edit button
                    st.markdown('<div class="tag-container">', unsafe_allow_html=True)
                    # Adjusted column widths to give more space to the edit button
                    col1, col2, col3 = st.columns([1.5, 1.5, 1])
                    with col1:
                        st.markdown(f'<div class="status-tag {status_class}">{status_text}</div>', unsafe_allow_html=True)
                    
                    with col2:
                        # Show sold to name if status is not available
                        if item.get('sale_status') != 'available' and item.get('sold_to'):
                            st.markdown(f'<div class="status-tag status-sold-to">👤 {item["sold_to"]}</div>', unsafe_allow_html=True)
                        
                    with col3:
                        if st.button(t('edit'), key=f"edit_{item['id']}", type="secondary", use_container_width=True):
                            st.session_state.editing_item = item
                            st.session_state.show_edit_modal = True
                            st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

        elif st.session_state.current_page != 'sold_to':
            st.info(t('no_items_found', status=st.session_state.current_page.replace('_', ' ')))

    elif st.session_state.current_page == 'add':
        st.title(t('add_item'))
        
        with st.form("add_item_form"):
            # Wrap the entire form in the compact-form class
            st.markdown('<div class="compact-form">', unsafe_allow_html=True)
            
            # Name field
            name = st.text_input(t('item_name'))
            
            # Price fields in a row
            col1, col2 = st.columns(2)
            with col1:
                price_usd = st.number_input("USD", min_value=0, value=0)
            with col2:
                price_local = st.number_input("LOCAL", min_value=0, value=0)
            
            # Status and sold_to in a row
            col1, col2 = st.columns([3, 2])
            with col1:
                status_options = {
                    'available': ('🏷️ ' + t('status_available'), 'status-available'),
                    'paid_pending_pickup': ('💰 ' + t('status_paid'), 'status-paid'),
                    'claimed_not_paid': ('⏳ ' + t('status_claimed'), 'status-claimed'),
                    'paid_picked_up': ('✅ ' + t('status_complete'), 'status-complete')
                }
                
                status_display = {text: key for key, (text, _) in status_options.items()}
                
                new_status_text = st.radio(
                    "Status",
                    options=list(status_display.keys()),
                    horizontal=True,
                    label_visibility="collapsed"
                )
                selected_status = status_display[new_status_text]
            
            with col2:
                sold_to = ""
                if selected_status != 'available':
                    sold_to = st.text_input("Sold to", label_visibility="collapsed", placeholder="Sold to")
            
            # Optional image upload
            image = st.file_uploader(t('upload_image'), type=["jpg", "jpeg", "png"])
            
            if st.form_submit_button(t('add_item_button')):
                if not name:
                    st.error(t('fill_required_fields'))
                else:
                    item_data = {
                        "name": name,
                        "price_usd": int(price_usd) if price_usd > 0 else None,
                        "price_local": int(price_local) if price_local > 0 else None,
                        "user_id": st.session_state.user.id,
                        "sale_status": selected_status,
                        "is_sold": selected_status == 'paid_picked_up'
                    }
                    if selected_status != 'available' and sold_to:
                        item_data['sold_to'] = sold_to
                    
                    new_item = add_item(item_data, image)
                    if new_item:
                        st.success(t('item_added'))
                        # Clear the cache to force reload of items
                        st.cache_data.clear()
                        # Switch to the available items view
                        st.session_state.current_page = 'available'
                        st.rerun()
            
            st.markdown('</div>', unsafe_allow_html=True)

    elif st.session_state.current_page == 'photos':
        st.title(t('generate_photos'))
        
        # Style selection
        style = st.radio(t('choose_photo_style'), [t('overlay'), t('extended')], horizontal=True)
        style = style.lower()
        
        # Load items and filter for available items only
        items = load_items()
        available_items = [item for item in items if not item.get('is_sold')]
        
        if available_items:
            # Add download all button
            all_photos = []
            
            st.write(t('loading_photos'))
            
            # Create a grid layout
            cols = st.columns(3)
            for i, item in enumerate(available_items):
                if item.get('image_url'):
                    with cols[i % 3]:
                        # Try to use pre-generated sales photo
                        sales_photo = None
                        if style == "overlay" and item.get('sales_overlay_url'):
                            response = requests.get(item['sales_overlay_url'])
                            if response.status_code == 200:
                                sales_photo = response.content
                        elif style == "extended" and item.get('sales_extended_url'):
                            response = requests.get(item['sales_extended_url'])
                            if response.status_code == 200:
                                sales_photo = response.content
                        
                        # Only generate if not available in storage
                        if not sales_photo:
                            sales_photo = generate_sales_photo(
                                item['image_url'],
                                item.get('price_usd'),
                                item.get('price_local'),
                                item['name'],
                                style,
                                item['id']
                            )
                            # Store the generated photo for future use
                            if sales_photo:
                                generate_and_store_sales_photos(
                                    item['id'],
                                    item['image_url'],
                                    item.get('price_usd'),
                                    item.get('price_local'),
                                    item['name']
                                )
                        
                        if sales_photo:
                            # Format price text for caption
                            if item.get('price_usd') and item.get('price_local'):
                                price_text = f"${item['price_usd']} USD / {item['price_local']} Moneda Local"
                            elif item.get('price_usd'):
                                price_text = f"${item['price_usd']} USD"
                            elif item.get('price_local'):
                                price_text = f"{item['price_local']} Moneda Local"
                            else:
                                price_text = ""
                            
                            st.image(BytesIO(sales_photo), caption=f"{item['name']} - {price_text}", width=200)
                            all_photos.append({
                                'name': item['name'],
                                'photo': sales_photo
                            })
                else:
                    st.warning(f"No image available for {item['name']}")
            
            # Add download all button if we have photos
            if all_photos:
                import zipfile
                
                # Create a ZIP file containing all photos
                zip_buffer = BytesIO()
                with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                    for photo in all_photos:
                        zip_file.writestr(
                            f"sales_photo_{photo['name'].lower().replace(' ', '_')}.jpg",
                            photo['photo']
                        )
                
                # Add download all button
                st.download_button(
                    label=t('download_all'),
                    data=zip_buffer.getvalue(),
                    file_name="all_sales_photos.zip",
                    mime="application/zip",
                    key="download_all"
                )
        else:
            st.info(t('no_available_items')) 