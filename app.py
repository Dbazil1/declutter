import streamlit as st
import asyncio
import os
from urllib.parse import urlparse

# Import services
from services.data_service import init_supabase, init_postgrest, load_items
from services.auth_service import logout, restore_auth_from_cookies

# Import UI components
from components.ui_components import apply_custom_css, render_sidebar_nav, render_login_ui
from components.item_components import render_add_item_form

# Import page renderers
from views.items_page import render_items_page
from views.photos_page import render_photos_page
from views.public_links_page import render_public_links_page
from views.public_page import render_public_page
from views.settings_page import render_settings_page

# Set page config
st.set_page_config(
    page_title="Declutter",
    page_icon="🏠",
    layout="wide"
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

# Handle public page route if code is provided
if public_link_code:
    render_public_page(public_link_code)
else:
    # Regular app flow
    if st.session_state.user is None:
        # Show login UI
        render_login_ui()
    else:
        # Get user's first name from the database
        user_info = st.session_state.supabase.table('users')\
            .select('first_name')\
            .eq('id', st.session_state.user.id)\
            .execute()
        
        first_name = user_info.data[0]['first_name'] if user_info.data else 'User'
        
        # Render sidebar navigation
        render_sidebar_nav(
            current_page=st.session_state.current_page,
            first_name=first_name,
            on_logout=logout
        )

        # Load items (used by multiple pages)
        items = load_items()

        # Main content
        if st.session_state.current_page in ['all', 'available', 'paid_ready', 'claimed', 'complete', 'sold_to']:
            render_items_page(st.session_state.current_page, items, first_name)
        elif st.session_state.current_page == 'add':
            render_add_item_form(rerun_callback=st.rerun)
        elif st.session_state.current_page == 'photos':
            render_photos_page(items)
        elif st.session_state.current_page == 'public_links':
            render_public_links_page()
        elif st.session_state.current_page == 'settings':
            render_settings_page()