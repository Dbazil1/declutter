import streamlit as st
import asyncio
import os
from urllib.parse import urlparse
from views.home_page import render_home_page
from views.settings_page import render_settings_page
from views.public_links_page import render_public_links_page
from services.auth_service import get_current_user, handle_auth_state
from utils.translation_utils import t
import traceback

# Import services
from services.data_service import init_supabase, init_postgrest, load_items
from services.auth_service import logout, restore_auth_from_cookies

# Import UI components
from components.ui_components import apply_custom_css, render_sidebar_nav, render_login_ui
from components.item_components import render_add_item_form

# Import page renderers
from views.items_page import render_items_page
from views.photos_page import render_photos_page
from views.public_page import render_public_page

# Set development mode flag
is_development = os.getenv('ENVIRONMENT', '').lower() == 'development'

# Configure the page
st.set_page_config(
    page_title="Declutter",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS
apply_custom_css()

# Initialize session state
if 'supabase' not in st.session_state:
    st.session_state.supabase = init_supabase()

if 'user' not in st.session_state:
    st.session_state.user = None
    # Try to restore authentication from cookies
    restore_auth_from_cookies()

if 'postgrest_client' not in st.session_state:
    asyncio.run(init_postgrest())

if 'current_page' not in st.session_state:
    st.session_state.current_page = 'available'

if 'auth_state' not in st.session_state:
    st.session_state.auth_state = None

# Initialize language
if 'language' not in st.session_state:
    st.session_state.language = 'en'

# Store base URL for public links
if 'base_url' not in st.session_state:
    # Try to get from environment variable first
    base_url = os.getenv('PUBLIC_URL')
    if not base_url:
        # Fallback to localhost for development
        base_url = 'http://localhost:8501'
    st.session_state.base_url = base_url

# Check query parameters for public link code
public_link_code = st.query_params.get("code", None)

# Handle authentication state
st.session_state.auth_state = handle_auth_state()

# Handle public page route if code is provided
if public_link_code:
    render_public_page(public_link_code)
elif st.session_state.auth_state != "authenticated" or not st.session_state.user:
    # Show login UI if not authenticated or user object is missing
    render_login_ui()
else:
    # User is authenticated, proceed with the main app
    try:
        # Get user's first name from the database
        try:
            user_info = st.session_state.supabase.table('users')\
                .select('first_name')\
                .eq('id', st.session_state.user.id)\
                .execute()
            
            first_name = 'User'  # Default value
            if user_info and hasattr(user_info, 'data') and user_info.data:
                first_name = user_info.data[0].get('first_name', 'User')
                
            if is_development:
                st.write(f"Current user: {first_name} (ID: {st.session_state.user.id})")
        except Exception as e:
            # If there's an error getting user info, use a default name
            if is_development:
                st.error(f"Error getting user info: {str(e)}")
                st.error(traceback.format_exc())
            first_name = 'User'
        
        # Render sidebar navigation
        render_sidebar_nav(
            current_page=st.session_state.current_page,
            first_name=first_name,
            on_logout=logout
        )

        # Load items (used by multiple pages)
        try:
            items = load_items()
        except Exception as e:
            if is_development:
                st.error(f"Error loading items: {str(e)}")
                st.error(traceback.format_exc())
            items = []
            st.warning("Could not load your items. Please try refreshing the page.")

        # Main content rendering based on current_page
        if st.session_state.current_page == 'home':
             render_home_page() # Added home page rendering
        elif st.session_state.current_page in ['all', 'available', 'paid_ready', 'claimed', 'complete', 'sold_to']:
            render_items_page(st.session_state.current_page, items, first_name)
        elif st.session_state.current_page == 'add':
            render_add_item_form(rerun_callback=st.rerun)
        elif st.session_state.current_page == 'photos':
            render_photos_page(items)
        elif st.session_state.current_page == 'public_links':
            render_public_links_page()
        elif st.session_state.current_page == 'settings':
            render_settings_page()
        else:
            # Default to available items page if current_page is unknown
            st.session_state.current_page = 'available'
            render_items_page(st.session_state.current_page, items, first_name)

    except Exception as e:
        st.error("An error occurred while loading the application. Please try again or contact support.")
        if is_development:
            st.error(f"Main App Error: {str(e)}")
            st.error(traceback.format_exc())

# Debug output in development mode
if is_development:
    st.write("--- Debug Information ---")
    st.write(f"Current Page: {st.session_state.current_page}")
    st.write(f"Auth State: {st.session_state.auth_state}")
    st.write(f"User Object: {st.session_state.user}")
    st.write("--- End Debug Information ---")