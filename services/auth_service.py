import streamlit as st
import traceback
import json
from utils.translation_utils import t
from services.data_service import update_user_whatsapp
import os
from supabase import create_client
from auth_state import set_user, store_auth_token, get_auth_token, clear_auth

# Set development mode flag
is_development = os.getenv('ENVIRONMENT', '').lower() == 'development'

def sign_in_user(email: str, password: str):
    """Sign in a user with email and password."""
    try:
        if not email or not password:
            st.error("Please enter both email and password")
            return False
            
        response = st.session_state.supabase.auth.sign_in_with_password({"email": email, "password": password})
        store_auth_token(response.session.access_token)
        set_user(response.user)
        return True
    except Exception as e:
        st.error(f"Login failed: {str(e)}")
        return False

# Authentication functions
def login(email: str, password: str):
    # Call the sign_in_user function for backwards compatibility
    return sign_in_user(email, password)

def signup(email: str, password: str, first_name: str, last_name: str):
    try:
        # Trim whitespace from inputs
        email = email.strip() if email else ""
        first_name = first_name.strip() if first_name else ""
        last_name = last_name.strip() if last_name else ""
        
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
        
        # Get WhatsApp info if provided
        whatsapp_phone = None
        share_whatsapp = False
        
        if 'whatsapp_info' in st.session_state:
            whatsapp_phone = st.session_state.whatsapp_info.get('phone')
            share_whatsapp = st.session_state.whatsapp_info.get('share', False)
            
            if is_development:
                st.write(f"WhatsApp info in session: {whatsapp_phone}, Share: {share_whatsapp}")
            
        st.write("Attempting to sign up...")
        
        try:
            # Create a service role client for auth operations
            service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            url = os.getenv('SUPABASE_URL')
            service_client = create_client(url, service_key)
            
            # Create auth user with email and password using service role
            auth = service_client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": {
                        "first_name": first_name,
                        "last_name": last_name
                    }
                }
            })
            
            if auth.user:
                # Debug output to verify user info from auth response
                if is_development:
                    st.write(f"Auth user ID: {auth.user.id}")
                    st.write(f"Auth user email from response: {auth.user.email}")
                    st.write(f"Auth user metadata: {auth.user.user_metadata}")
                
                # Store user temporarily in session state to allow direct WhatsApp update
                temp_user = st.session_state.user
                st.session_state.user = auth.user
                
                # Check if the user already has been added to the public.users table
                # This might happen automatically via database trigger
                user_exists_query = service_client.table('users').select('*').eq('id', auth.user.id).execute()
                
                # Only create user record if it doesn't already exist
                if not user_exists_query.data:
                    if is_development:
                        st.warning("Trigger did not create user record. Creating manually...")
                
                    # Create the user record in our users table with name fields
                    user_data = {
                        'id': auth.user.id,  # Use the same ID from auth.users
                        'email': email,      # Add email to public.users table
                        'first_name': first_name,
                        'last_name': last_name,
                        'role': 'user'
                    }
                    
                    # Add WhatsApp information if available
                    if whatsapp_phone:
                        user_data['whatsapp_phone'] = whatsapp_phone
                        user_data['share_whatsapp_for_items'] = share_whatsapp
                    
                    # Debug output in development mode
                    if is_development:
                        st.write("User data to be inserted:")
                        st.write(user_data)
                    
                    try:
                        response = service_client.table('users').insert(user_data).execute()
                        
                        # Debug output in development mode
                        if is_development:
                            st.write("Insert response:")
                            st.write(response.data if hasattr(response, 'data') else "No response data")
                    except Exception as db_error:
                        # Check if this is a duplicate key error
                        error_str = str(db_error)
                        if "duplicate key" in error_str and "users_pkey" in error_str:
                            st.error(t('account_already_exists'))
                            # Try to clean up the auth user since we couldn't create the profile
                            try:
                                # This might not always work depending on permissions
                                service_client.auth.admin.delete_user(auth.user.id)
                            except:
                                pass
                            return False
                        else:
                            if is_development:
                                st.error(f"Database error: {str(db_error)}")
                                st.error(traceback.format_exc())
                            # Re-raise if it's a different error
                            raise
                else:
                    # User was created by trigger, but may not have WhatsApp info
                    if whatsapp_phone:
                        # Directly update WhatsApp info using the update function
                        whatsapp_updated = update_user_whatsapp(whatsapp_phone, share_whatsapp)
                        
                        if is_development:
                            if whatsapp_updated:
                                st.success("WhatsApp information updated successfully")
                            else:
                                st.error("Failed to update WhatsApp information")
                
                # Restore original user (if any)
                st.session_state.user = temp_user
                
                st.success("Account created successfully! Please proceed to login.")
                return True
            
        except Exception as auth_error:
            # Check for Supabase auth errors that indicate duplicate email
            error_str = str(auth_error)
            if "User already registered" in error_str or "already exists" in error_str:
                st.error(t('account_already_exists'))
                return False
            else:
                if is_development:
                    st.error(f"Auth error: {str(auth_error)}")
                    st.error(traceback.format_exc())
                # Re-raise if it's a different error
                raise
                
    except Exception as e:
        # Generic error handling
        st.error(t('signup_failed'))
        # Always show error details - helps with debugging in production
        st.error(f"Error details: {str(e)}")
        st.error(traceback.format_exc())
        return False

def logout():
    """Log out the current user."""
    try:
        st.session_state.supabase.auth.sign_out()
    except Exception:
        pass
    clear_auth()
    st.rerun()

# Function to save authentication info to cookies
def save_auth_to_cookie(session):
    """Save authentication data to cookies for persistent login"""
    try:
        if is_development:
            st.write("Debug: Saving auth tokens to session state")
            
        # Save tokens in session state (these persist between Streamlit reruns)
        if session and hasattr(session, 'access_token'):
            st.session_state['auth_token'] = session.access_token
            st.session_state['refresh_token'] = session.refresh_token
            
            if is_development:
                masked_token = session.access_token[:10] + "..." if session.access_token else "None" 
                st.write(f"Debug: Saved auth token: {masked_token}")
                st.write(f"Debug: Saved refresh token: {'Yes' if session.refresh_token else 'No'}")
        else:
            if is_development:
                st.write("Debug: No valid session to save")
    except Exception as e:
        if is_development:
            st.error(f"Error saving auth to cookies: {str(e)}")
            st.error(traceback.format_exc())

# Function to clear authentication cookies
def clear_auth_cookies():
    try:
        # Clear from session state
        if 'auth_token' in st.session_state:
            del st.session_state['auth_token']
        if 'refresh_token' in st.session_state:
            del st.session_state['refresh_token']
    except Exception as e:
        st.error(f"Error clearing auth from session state: {str(e)}")

# Function to restore authentication data from cookies
def restore_auth_from_cookies():
    """Attempt to restore authentication from cookies."""
    try:
        session = st.session_state.supabase.auth.get_session()
        if session:
            store_auth_token(session.access_token)
            user = st.session_state.supabase.auth.get_user(session.access_token)
            if user:
                set_user(user.user)
                return True
    except Exception:
        pass
    return False

def get_current_user():
    """Get the current authenticated user with validation."""
    from auth_state import get_user
    return get_user()

def handle_auth_state():
    """Handle authentication state and token refresh."""
    # Check if we have a token but no user
    if get_auth_token() and not get_current_user():
        try:
            # Try to get the user with the stored token
            user = st.session_state.supabase.auth.get_user(get_auth_token())
            if user:
                set_user(user.user)
                return "authenticated"
            else:
                return "needs_login"
        except Exception:
            clear_auth()
            return "needs_login"
    elif get_current_user():
        return "authenticated"
    else:
        return "needs_login" 