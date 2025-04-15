import streamlit as st
import time
import os

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
        if st.button("🏷️", key="nav_available", help=t('available')):
            st.session_state.current_page = "available"
            st.rerun()
    
    # Paid Pending icon button - Blue 
    with cols[1]:
        if st.button("💰", key="nav_paid_ready", help=t('paid_ready')):
            st.session_state.current_page = "paid_ready"
            st.rerun()
    
    # Claimed icon button - Purple
    with cols[2]:
        if st.button("⏳", key="nav_claimed", help=t('claimed')):
            st.session_state.current_page = "claimed"
            st.rerun()
    
    # Complete icon button - Green
    with cols[3]:
        if st.button("✅", key="nav_complete", help=t('complete')):
            st.session_state.current_page = "complete"
            st.rerun()
    
    # Sold To icon button - Gray
    with cols[4]:
        if st.button("👤", key="nav_sold_to", help=t('sold_to')):
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
        "Language / Idioma",
        options=[('English', 'en'), ('Español', 'es')],
        format_func=lambda x: x[0],
        key='language_selector',
        index=0 if st.session_state.language == 'en' else 1
    )
    if selected_lang[1] != st.session_state.language:
        st.session_state.language = selected_lang[1]

def render_login_ui():
    from utils.translation_utils import t
    
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
                    from services.auth_service import login
                    if login(email, password):
                        # Clear the last signup email after successful login
                        if 'last_signup_email' in st.session_state:
                            del st.session_state.last_signup_email
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
                            from services.auth_service import signup
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