import streamlit as st
import asyncio
import os
import sys
from urllib.parse import urlparse
import traceback
from supabase import create_client
from auth_state import init_auth_state, is_authenticated

# Add the current directory to the Python path to help with module discovery
app_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, app_dir)

# Show debugging information if needed
if os.getenv('DEBUG_IMPORTS', '').lower() == 'true':
    st.write("Python path:", sys.path)
    st.write("Current directory:", os.getcwd())
    st.write("App directory:", app_dir)
    if os.path.exists("views"):
        st.write("Views directory exists with files:", os.listdir("views"))
    else:
        st.write("Views directory does not exist")

# Import required modules with error handling
try:
    # Views
    from views.home_page import render_home_page
    from views.settings_page import render_settings_page
    from views.public_links_page import render_public_links_page
    from views.items_page import render_items_page
    from views.photos_page import render_photos_page
    from views.public_page import render_public_page
    
    # Services
    from services.auth_service import get_current_user, handle_auth_state
    from services.auth_service import logout, restore_auth_from_cookies
    from services.data_service import init_supabase, init_postgrest, load_items
    
    # UI components
    from components.ui_components import apply_custom_css, render_sidebar_nav, render_login_ui
    from components.item_components import render_add_item_form
    
    # Utils
    from utils.translation_utils import t
except ImportError as e:
    st.error(f"Import error: {str(e)}")
    st.error(traceback.format_exc())
    st.error("This error indicates Python cannot find the modules.")
    st.error("Possible solutions:")
    st.error("1. Make sure you have __init__.py files in all subdirectories")
    st.error("2. Run with proper working directory: python -m streamlit run app.py")
    st.error("3. Set the PYTHONPATH environment variable to include your project root")
    st.stop()

# Set development mode flag
is_development = os.getenv('ENVIRONMENT', '').lower() == 'development'

# Debug function to check auth status
def debug_auth_status():
    """Display debug information about the current authentication status"""
    if not is_development:
        return
        
    st.sidebar.markdown("---")
    st.sidebar.write("### Debug Information")
    
    # Create a service role client for database operations
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    url = os.getenv('SUPABASE_URL')
    service_client = create_client(url, service_key)
    
    # Check if user exists in session
    user = get_current_user()
    if user and hasattr(user, 'id'):
        st.sidebar.write("✅ User is authenticated")
        st.sidebar.write(f"User ID: {user.id}")
        if hasattr(user, 'email'):
            st.sidebar.write(f"Email: {user.email}")
            
        # Check if user has a valid token
        try:
            # Test a simple query to see if auth is valid
            test_result = service_client.table('users').select('id').eq('id', user.id).limit(1).execute()
            if test_result.data:
                st.sidebar.write("✅ Supabase connection is valid")
            else:
                st.sidebar.write("❌ User record not found in database")
        except Exception as e:
            st.sidebar.write("❌ Error querying database")
            st.sidebar.write(f"Error: {str(e)}")
    else:
        st.sidebar.write("❌ User is not authenticated")
    
    # Show session state keys
    st.sidebar.write("Session state keys:")
    st.sidebar.write(list(st.session_state.keys()))

# Configure the page
st.set_page_config(
    page_title="Declutter",
    page_icon="🧹",
    layout="wide",
    initial_sidebar_state="auto"
)

# Apply custom CSS
apply_custom_css()

# Initialize auth state
init_auth_state()

# Initialize session state
if 'supabase' not in st.session_state:
    st.session_state.supabase = init_supabase()

# Try to restore authentication from cookies
if not is_authenticated():
    restore_auth_from_cookies()

if 'postgrest_client' not in st.session_state:
    from services.data_service import init_postgrest
    # Simply call the function directly, as it's now synchronous
    init_postgrest()

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
    if not is_authenticated():
        # Show login UI
        render_login_ui()
        st.stop()
    else:
        # Create a service role client for database operations
        service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        url = os.getenv('SUPABASE_URL')
        service_client = create_client(url, service_key)
        
        # Get user's first name from the database
        try:
            user = get_current_user()
            user_info = service_client.table('users')\
                .select('first_name')\
                .eq('id', user.id)\
                .execute()
            
            first_name = 'User'  # Default value
            if user_info and hasattr(user_info, 'data') and user_info.data:
                first_name = user_info.data[0].get('first_name', 'User')
                
            if is_development:
                st.write(f"Current user: {first_name} (ID: {user.id})")
        except Exception as e:
            # If there's an error getting user info, use a default name
            if is_development:
                st.error(f"Error getting user info: {str(e)}")
                import traceback
                st.error(traceback.format_exc())
            first_name = 'User'
        
        # Display debug information if in development mode
        if is_development:
            debug_auth_status()
        
        # Render sidebar navigation
        render_sidebar_nav(
            current_page=st.session_state.current_page,
            first_name=first_name,
            on_logout=logout
        )

        # Show mobile navigation hint for first-time users
        # Initialize session state for showing hint
        if 'mobile_nav_hint_shown' not in st.session_state:
            st.session_state.mobile_nav_hint_shown = False
            
        # Add a hint for mobile users about the sidebar
        st.markdown("""
            <style>
                @media (max-width: 768px) {
                    .mobile-nav-hint {
                        position: relative;
                        padding: 10px 15px;
                        margin-bottom: 15px;
                        background-color: #f0f7ff;
                        border-left: 5px solid #0085ff;
                        border-radius: 5px;
                        animation: fadeOut 8s forwards;
                        font-size: 14px;
                    }
                    @keyframes fadeOut {
                        0% { opacity: 1; }
                        80% { opacity: 1; }
                        100% { opacity: 0; visibility: hidden; }
                    }
                }
                @media (min-width: 769px) {
                    .mobile-nav-hint {
                        display: none;
                    }
                }
            </style>
            <div class="mobile-nav-hint">
                <b>Tip:</b> Tap the menu icon <span style="background-color:rgba(0,0,0,0.1);border-radius:50%;padding:4px 8px;margin:0 3px;">☰</span> in the top-left corner for navigation options.
            </div>
        """, unsafe_allow_html=True)
        st.session_state.mobile_nav_hint_shown = True

        # Load items (used by multiple pages)
        try:
            items = load_items()
        except Exception as e:
            if is_development:
                st.error(f"Error loading items: {str(e)}")
                import traceback
                st.error(traceback.format_exc())
            items = []
            st.warning("Could not load your items. Please try refreshing the page.")

        # Main content with error handling for each page
        try:
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
        except Exception as page_error:
            st.error("An error occurred while loading this page. Please try again or contact support.")
            if is_development:
                st.error(f"Page error: {str(page_error)}")
                import traceback
                st.error(traceback.format_exc())

# Debug output in development mode
if is_development:
    st.write("Debug: Session state initialized")
    st.write(f"Debug: Current page: {st.session_state.current_page}")
    st.write(f"Debug: User: {get_current_user()}")

# Main app logic
try:
    # Handle authentication state
    auth_state = handle_auth_state()
    
    if is_development:
        st.write(f"Debug: Auth state after handling: {auth_state}")
    
    if auth_state == "needs_login":
        st.session_state.current_page = 'home'
        # Since we're changing page to 'home', we need to render it
        render_home_page()
    elif auth_state == "authenticated":
        # Only proceed if we have a valid user
        user = get_current_user()
        if user and hasattr(user, 'id'):
            if is_development:
                st.write(f"Debug: User authenticated: {user.email}")
            
            # Only render home page here if it wasn't already rendered above
            if st.session_state.current_page == 'home':
                render_home_page()
        else:
            if is_development:
                st.write("Debug: User object is invalid or missing ID")
            st.error("Authentication error. Please try logging in again.")
            st.session_state.current_page = 'home'
            render_home_page()
    else:
        if is_development:
            st.write("Debug: Auth state is None or invalid")
        st.error("Authentication error. Please try logging in again.")
        st.session_state.current_page = 'home'
        render_home_page()

except Exception as e:
    if is_development:
        st.error(f"Error in main app: {str(e)}")
        st.error(traceback.format_exc())
    st.error("An error occurred. Please try again or contact support.")