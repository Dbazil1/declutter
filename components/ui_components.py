import streamlit as st
import time
import os
import traceback
from utils.translation_utils import t
from services.auth_service import sign_in_user

# Set development mode flag
is_development = os.getenv('ENVIRONMENT', '').lower() == 'development'

def show_error_message(error, details=None):
    """Display an error message with optional details in development mode."""
    st.error(error)
    if is_development and details:
        st.error(f"Details: {details}")
        st.error(traceback.format_exc())

def show_success_message(message):
    """Display a success message."""
    st.success(message)
    if is_development:
        st.write(f"Debug: {message}")

def apply_custom_css():
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
            /* Navigation filter buttons */
            button[data-testid="baseButton-secondary"]:has(div:contains("🏷️")) {
                background-color: #F29F05 !important;
                color: white !important;
                border-radius: 50% !important;
                width: 40px !important;
                height: 40px !important;
                padding: 0 !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                border: none !important;
            }
            button[data-testid="baseButton-secondary"]:has(div:contains("💰")) {
                background-color: #048ABF !important;
                color: white !important;
                border-radius: 50% !important;
                width: 40px !important;
                height: 40px !important;
                padding: 0 !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                border: none !important;
            }
            button[data-testid="baseButton-secondary"]:has(div:contains("⏳")) {
                background-color: #A63C94 !important;
                color: white !important;
                border-radius: 50% !important;
                width: 40px !important;
                height: 40px !important;
                padding: 0 !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                border: none !important;
            }
            button[data-testid="baseButton-secondary"]:has(div:contains("✅")) {
                background-color: #66B794 !important;
                color: white !important;
                border-radius: 50% !important;
                width: 40px !important;
                height: 40px !important;
                padding: 0 !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                border: none !important;
            }
            button[data-testid="baseButton-secondary"]:has(div:contains("👤")) {
                background-color: #E0E0E0 !important;
                color: #333333 !important;
                border-radius: 50% !important;
                width: 40px !important;
                height: 40px !important;
                padding: 0 !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                border: none !important;
            }
            /* Utility icon buttons */
            button[data-testid="baseButton-secondary"]:has(div:contains("🔗")),
            button[data-testid="baseButton-secondary"]:has(div:contains("⚙️")) {
                background-color: #f0f0f0 !important;
                color: #333333 !important;
                border-radius: 50% !important;
                width: 40px !important;
                height: 40px !important;
                padding: 0 !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
                border: none !important;
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
            /* Override for icon buttons */
            button[data-testid="baseButton-secondary"]:has(div:contains("🏷️")),
            button[data-testid="baseButton-secondary"]:has(div:contains("💰")),
            button[data-testid="baseButton-secondary"]:has(div:contains("⏳")),
            button[data-testid="baseButton-secondary"]:has(div:contains("✅")),
            button[data-testid="baseButton-secondary"]:has(div:contains("👤")),
            button[data-testid="baseButton-secondary"]:has(div:contains("🔗")),
            button[data-testid="baseButton-secondary"]:has(div:contains("⚙️")) {
                border-radius: 50% !important;
                width: 40px !important;
                height: 40px !important;
                padding: 0 !important;
                min-height: 0 !important;
                border: none !important;
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
            /* Fix for language dropdown width */
            .language-selector [data-testid="stSelectbox"],
            [key="login_language_selector"],
            [key="language_selector"] {
                min-width: 150px !important;
            }
            [data-testid="stSelectbox"] > div {
                min-width: 150px !important;
                max-width: 170px !important;
                height: auto !important;
                min-height: 38px !important;
            }
            /* Make dropdown options taller to fit emoji and text */
            [data-testid="stSelectbox"] ul li {
                height: auto !important;
                min-height: 38px !important;
                padding: 8px 12px !important;
                display: flex !important;
                align-items: center !important;
            }
            /* Center the login language selector */
            [data-testid="stSelectbox"][aria-label=""] {
                width: auto !important;
                margin: 0 auto !important;
            }
            /* For sidebar language selector */
            .sidebar .stSelectbox > div {
                width: 100% !important;
            }
            /* Icon button styles */
            .icon-button {
                padding: 0.5rem !important;
                height: 44px !important;
                width: 44px !important;
                border-radius: 50% !important;
                display: inline-flex !important;
                align-items: center !important;
                justify-content: center !important;
                font-size: 1.25rem !important;
                margin: 4px !important;
                min-height: 0 !important;
            }
            .icon-row {
                display: flex !important;
                flex-wrap: wrap !important;
                justify-content: center !important;
                gap: 4px !important;
            }
            .filter-button-row {
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 8px;
                margin: 8px 0;
            }

            /* Mobile responsive adjustments */
            @media (max-width: 768px) {
                /* Increase button size for touch targets */
                [data-testid="baseButton-secondary"] {
                    min-height: 44px !important;
                    min-width: 44px !important;
                    padding: 10px !important;
                }
                
                /* Ensure inputs are large enough to tap */
                .stTextInput input, .stNumberInput input, .stSelectbox > div {
                    min-height: 44px !important;
                    font-size: 16px !important; /* Prevents iOS zoom on focus */
                }
                
                /* Style the collapse/expand button */
                [data-testid="collapsedControl"] {
                    height: 50px !important;
                    width: 50px !important;
                    border-radius: 25px !important;
                    background-color: rgba(0, 0, 0, 0.1) !important;
                    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2) !important;
                    z-index: 999 !important;
                    animation: pulse 2s ease-in-out infinite, glow 4s ease-in-out 1;
                }
                
                /* Replace the default arrow with hamburger icon */
                [data-testid="collapsedControl"] svg {
                    display: none !important; /* Hide the default arrow icon */
                }
                
                /* Create hamburger icon using ::before pseudo-element */
                [data-testid="collapsedControl"]::before {
                    content: "☰" !important; /* Unicode hamburger symbol */
                    font-size: 24px !important;
                    color: #333 !important;
                    position: absolute !important;
                    top: 50% !important;
                    left: 50% !important;
                    transform: translate(-50%, -50%) !important;
                    display: flex !important;
                    justify-content: center !important;
                    align-items: center !important;
                }
                
                /* Style for the expanded sidebar button (X icon) */
                button[kind="header"]:not([data-testid="collapsedControl"]),
                .st-emotion-cache-1egp75f,
                [data-testid="baseButton-headerNoPadding"] {
                    height: 50px !important;
                    width: 50px !important;
                    border-radius: 25px !important;
                    background-color: rgba(0, 0, 0, 0.1) !important;
                    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2) !important;
                }
                
                /* Hide the default arrow on the expanded button */
                button[kind="header"]:not([data-testid="collapsedControl"]) svg,
                .st-emotion-cache-1egp75f svg,
                [data-testid="baseButton-headerNoPadding"] svg {
                    display: none !important;
                }
                
                /* Add an X symbol to the expanded button */
                button[kind="header"]:not([data-testid="collapsedControl"])::before,
                .st-emotion-cache-1egp75f::before,
                [data-testid="baseButton-headerNoPadding"]::before {
                    content: "×" !important; /* Unicode X symbol */
                    font-size: 30px !important;
                    font-weight: bold !important;
                    color: #333 !important;
                    position: absolute !important;
                    top: 50% !important;
                    left: 50% !important;
                    transform: translate(-50%, -50%) !important;
                    display: flex !important;
                    justify-content: center !important;
                    align-items: center !important;
                }
                
                /* Subtle animation to draw attention to the button */
                @keyframes pulse {
                    0% { transform: scale(1); }
                    50% { transform: scale(1.05); }
                    100% { transform: scale(1); }
                }
                
                /* Initial glow animation for first-time users */
                @keyframes glow {
                    0% { box-shadow: 0 0 5px rgba(0, 0, 0, 0.2); }
                    50% { box-shadow: 0 0 10px rgba(0, 133, 255, 0.4); }
                    100% { box-shadow: 0 0 5px rgba(0, 0, 0, 0.2); }
                }
                
                /* Make the icon inside more visible */
                [data-testid="collapsedControl"] svg {
                    fill: #333 !important;
                    width: 25px !important;
                    height: 25px !important;
                }
                
                /* Make sure filter buttons are easily tappable */
                button[data-testid="baseButton-secondary"]:has(div:contains("🏷️")),
                button[data-testid="baseButton-secondary"]:has(div:contains("💰")),
                button[data-testid="baseButton-secondary"]:has(div:contains("⏳")),
                button[data-testid="baseButton-secondary"]:has(div:contains("✅")),
                button[data-testid="baseButton-secondary"]:has(div:contains("👤")) {
                    width: 50px !important;
                    height: 50px !important;
                }
                
                /* Adjust spacing for mobile */
                .compact-form {
                    padding: 1rem 0.5rem !important;
                }
                
                /* Ensure form rows stack on mobile */
                .compact-form .row {
                    flex-direction: column !important;
                    gap: 0.5rem !important;
                }
                
                /* Make tables and dataframes horizontally scrollable on mobile */
                [data-testid="stTable"], .dataframe-container {
                    overflow-x: auto !important;
                    -webkit-overflow-scrolling: touch !important;
                    max-width: 100% !important;
                    display: block !important;
                }
                
                /* Adjust font sizes for readability on mobile */
                [data-testid="stMarkdown"] {
                    font-size: 14px !important;
                }
                
                /* Ensure inputs don't get cut off */
                input, select, textarea {
                    max-width: 100% !important;
                    box-sizing: border-box !important;
                }
            }

            @media (max-width: 480px) {
                .login-container {
                    max-width: 100%;
                    margin: 1rem auto;
                    padding: 1rem;
                }
                
                .login-tagline {
                    font-size: 1.8rem;
                }
            }
        </style>
        """, unsafe_allow_html=True)

def render_sidebar_nav(current_page, first_name, on_logout):
    from utils.translation_utils import t
    
    st.sidebar.image("declutter-logo.png", use_container_width=True)
    
    # Keep All Items as full button
    if st.sidebar.button("📋 " + t('all_items'), key="nav_all", use_container_width=True):
        st.session_state.current_page = "all"
        st.rerun()
    
    # Create a row of columns for the filter buttons
    cols = st.sidebar.columns(5)
    
    # Available icon button - Yellow
    with cols[0]:
        if st.button("🏷️", key="nav_available", help=t('available'), use_container_width=True):
            st.session_state.current_page = "available"
            st.rerun()
    
    # Paid Pending icon button - Blue 
    with cols[1]:
        if st.button("💰", key="nav_paid_ready", help=t('paid_ready'), use_container_width=True):
            st.session_state.current_page = "paid_ready"
            st.rerun()
    
    # Claimed icon button - Purple
    with cols[2]:
        if st.button("⏳", key="nav_claimed", help=t('claimed'), use_container_width=True):
            st.session_state.current_page = "claimed"
            st.rerun()
    
    # Complete icon button - Green
    with cols[3]:
        if st.button("✅", key="nav_complete", help=t('complete'), use_container_width=True):
            st.session_state.current_page = "complete"
            st.rerun()
    
    # Sold To icon button - Gray
    with cols[4]:
        if st.button("👤", key="nav_sold_to", help=t('sold_to'), use_container_width=True):
            st.session_state.current_page = "sold_to"
            st.rerun()
    
    # Add main action buttons that still show text
    if st.sidebar.button("➕ " + t('add_item'), key="nav_add", use_container_width=True):
        st.session_state.current_page = "add"
        st.rerun()
    
    if st.sidebar.button("📸 " + t('generate_photos'), key="nav_photos", use_container_width=True):
        st.session_state.current_page = "photos"
        st.rerun()
    
    if st.sidebar.button("🔗 " + t('public_links'), key="nav_public_links", use_container_width=True):
        st.session_state.current_page = "public_links"
        st.rerun()
    
    # Settings and Logout as icon buttons in a row
    cols2 = st.sidebar.columns([1, 1, 3])
    
    # Settings icon button
    with cols2[0]:
        if st.button("⚙️", key="nav_settings", help=t('settings')):
            st.session_state.current_page = "settings"
            st.rerun()
    
    # Logout icon button
    with cols2[1]:
        if st.button("🚪", key="nav_logout", help=t('logout')):
            on_logout()
            st.rerun()

    # Add bazil-dot-studio logo at the very bottom
    st.sidebar.image("bazil-dot-studio.png", use_container_width=True)
    
    # Add contact developer link
    st.sidebar.markdown("""
        <div style="text-align: center; margin-top: 0px; margin-bottom: 10px;">
            <a href="http://bazil.contact" target="_blank" style="color: #666; text-decoration: none; font-size: 0.8rem;">
                Contact Developer
            </a>
        </div>
    """, unsafe_allow_html=True)

    # Add language selector at the very bottom
    st.sidebar.markdown("---")  # Add a divider
    selected_lang = st.sidebar.selectbox(
        "",  # Empty label for cleaner look
        options=[('🇺🇸 English', 'en'), ('🇲🇽 Español', 'es')],
        format_func=lambda x: x[0],
        key='language_selector',
        index=0 if st.session_state.language == 'en' else 1,
        label_visibility="collapsed"
    )
    if selected_lang[1] != st.session_state.language:
        st.session_state.language = selected_lang[1]

def render_login_ui():
    """Render the login UI."""
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
            with st.form("login_form_unique_key"):
                # Pre-fill email if coming from successful signup
                default_email = st.session_state.get('last_signup_email', '')
                email = st.text_input(t('email'), value=default_email, key='login_email')
                password = st.text_input(t('password'), type="password")
                submit = st.form_submit_button(t('login'))
                
                if submit:
                    if email and password:
                        success = sign_in_user(email, password)
                        if success:
                            # Clear the last signup email after successful login
                            if 'last_signup_email' in st.session_state:
                                del st.session_state.last_signup_email
                            st.success("Login successful!")
                            st.rerun()
                    else:
                        st.error("Please enter both email and password.")
        
        with tab2:  # Signup tab
            # Show success message above the form if exists
            if 'signup_success' in st.session_state:
                st.success(t('signup_success'))
                st.info(t('proceed_to_login'))
                del st.session_state.signup_success
 
            with st.form("signup_form_unique_key"):
                col1, col2 = st.columns(2)
                with col1:
                    first_name = st.text_input(t('first_name'))
                with col2:
                    last_name = st.text_input(t('last_name'))
                new_email = st.text_input(t('email'))
                new_password = st.text_input(t('password'), type="password")
                confirm_password = st.text_input(t('confirm_password'), type="password")
                
                # WhatsApp number input with clear country code format
                st.markdown("### " + t('whatsapp_optional_but_important'))
                st.markdown(t('whatsapp_fun_explanation'))
                col3, col4 = st.columns([1, 3])
                with col3:
                    country_code = st.text_input(t('country_code'), placeholder="+1", value="+")
                with col4:
                    phone_number = st.text_input(t('phone_number'), placeholder="123-456-7890")
                
                # Consent checkbox for WhatsApp
                whatsapp_consent = st.checkbox(t('whatsapp_consent'))
                
                submit = st.form_submit_button(t('signup'))
                
                if submit:
                    from services.auth_service import signup
                    # Trim whitespace from all inputs
                    first_name = first_name.strip() if first_name else ""
                    last_name = last_name.strip() if last_name else ""
                    new_email = new_email.strip() if new_email else ""
                    
                    if new_password != confirm_password:
                        st.error(t('passwords_match'))
                    elif not first_name or not last_name:
                        st.error(t('enter_names'))
                    else:
                        # Prepare WhatsApp info for updating after signup
                        if country_code and phone_number and whatsapp_consent:
                            full_phone = country_code.strip() + phone_number.strip().replace("-", "").replace(" ", "")
                            st.session_state.whatsapp_info = {
                                'phone': full_phone,
                                'share': whatsapp_consent
                            }
                            # Debug WhatsApp info in development
                            if os.getenv('ENVIRONMENT') == 'development':
                                st.write(f"Setting WhatsApp info in session: {full_phone}, Share: {whatsapp_consent}")
                        
                        with st.spinner(t('creating_account')):
                            if signup(new_email, new_password, first_name, last_name):
                                # Store success state and email
                                st.session_state.signup_success = True
                                st.session_state.last_signup_email = new_email
                                st.rerun()

    # Debug option - only visible in development
    if os.getenv('ENVIRONMENT') == 'development':
        if st.button("🔧 Debug Connection", key="debug_connection"):
            from services.data_service import debug_env
            debug_env()
            # Check if supabase client is initialized properly before accessing auth.url
            if 'supabase' in st.session_state and st.session_state.supabase and hasattr(st.session_state.supabase, 'auth'):
                try:
                    # Safely check the URL from the supabase client
                    st.write("Supabase connection status:", "Active" if st.session_state.supabase else "Not connected")
                    st.write("Supabase URL:", os.getenv("SUPABASE_URL", "Not set"))
                except Exception as e:
                    st.error(f"Error accessing Supabase client: {str(e)}")
            else:
                st.error("Supabase client not properly initialized.")

    # Add language selector at the bottom, centered
    st.markdown('<div style="display: flex; justify-content: center; margin-top: 20px;">', unsafe_allow_html=True)
    
    # Create a compact dropdown with just enough width
    selected_lang = st.selectbox(
        "",  # Empty label
        options=[('🇺🇸 English', 'en'), ('🇲🇽 Español', 'es')],
        format_func=lambda x: x[0],
        key='login_language_selector',
        index=0 if st.session_state.language == 'en' else 1,
        label_visibility="collapsed"
    )
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if selected_lang[1] != st.session_state.language:
        st.session_state.language = selected_lang[1] 