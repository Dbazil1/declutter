import streamlit as st
import traceback
import json
from utils.translation_utils import t
from services.data_service import update_user_whatsapp
import os
from supabase import create_client

# Set development mode flag
is_development = os.getenv('ENVIRONMENT', '').lower() == 'development'

# Authentication functions
def login(email: str, password: str):
    try:
        if not email or not password:
            st.error("Please enter both email and password")
            return False
            
        st.write("Attempting to sign in...")
        try:
            # Create a service role client for auth operations
            service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            url = os.getenv('SUPABASE_URL')
            service_client = create_client(url, service_key)
            
            # Use normal auth with the service client
            auth = service_client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            # Debug information about the auth response
            if is_development:
                st.write(f"Auth successful, user ID: {auth.user.id}")
                st.write(f"User email from auth: {auth.user.email}")
                st.write(f"User metadata: {auth.user.user_metadata}")
            
            st.session_state.user = auth.user
            st.session_state.auth_state = "authenticated"
            
            # Verify user exists in the users table and create if needed
            user_record = service_client.table('users').select('*').eq('id', auth.user.id).execute()
            
            if not user_record.data:
                # The user exists in auth.users but not in public.users
                # This can happen if the trigger failed or if we're migrating users
                if is_development:
                    st.warning("User not found in public.users table, creating record now...")
                
                # Try to extract first/last name from auth metadata
                metadata = auth.user.user_metadata if hasattr(auth.user, 'user_metadata') else {}
                first_name = metadata.get('first_name', email.split('@')[0])
                last_name = metadata.get('last_name', '')
                
                # Create the missing user record
                user_data = {
                    'id': auth.user.id,
                    'email': email,  # Add email to ensure it matches auth.users
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': 'user'
                }
                
                try:
                    insert_response = service_client.table('users').insert(user_data).execute()
                    if is_development:
                        st.success("User record created in public.users table")
                        st.write(f"Insert response: {insert_response.data if hasattr(insert_response, 'data') else None}")
                except Exception as create_error:
                    # Log error but don't fail login
                    if is_development:
                        st.error(f"Failed to create user record: {str(create_error)}")
                        st.error(traceback.format_exc())
            else:
                if is_development:
                    st.success(f"Found existing user record: {user_record.data}")
            
            # Clear all cached data when logging in
            st.cache_data.clear()
            
            # Store auth info in browser cookies
            save_auth_to_cookie(auth.session)
            
            # If the user has pending WhatsApp info to update, do it now
            if 'whatsapp_info' in st.session_state:
                whatsapp_info = st.session_state.whatsapp_info
                if is_development:
                    st.write(f"Updating WhatsApp info during login: {whatsapp_info['phone']}")
                update_result = update_user_whatsapp(
                    whatsapp_info['phone'], 
                    whatsapp_info['share']
                )
                # Remove the temporary data
                del st.session_state.whatsapp_info
                
                if is_development:
                    if update_result:
                        st.success("WhatsApp information updated during login")
                    else:
                        st.error("Failed to update WhatsApp information during login")
            
            st.session_state.current_page = "all"  # Redirect to all items page after login
            st.success("Login successful!")
            return True
            
        except Exception as auth_error:
            # Check for specific authentication errors
            error_str = str(auth_error)
            if "Invalid login credentials" in error_str:
                st.error("Invalid email or password")
            elif "Email not confirmed" in error_str:
                st.error("Please confirm your email address first")
            else:
                st.error(f"Login failed: {str(auth_error)}")
                # Show detailed error in development mode
                if is_development:
                    st.error(traceback.format_exc())
            return False
            
    except Exception as e:
        st.error(f"Login failed: {str(e)}")
        st.error(traceback.format_exc())
        return False

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
    """Log the user out and clear auth state"""
    try:
        if is_development:
            st.write("Debug: Logging out user")
            
        # Create a service role client for auth operations
        service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        url = os.getenv('SUPABASE_URL')
        service_client = create_client(url, service_key)
        
        # Sign out via Supabase API using service role
        if st.session_state.get('user') and hasattr(st.session_state.user, 'id'):
            # Admin signout of a specific user
            service_client.auth.admin.sign_out_user(st.session_state.user.id)
        
        # Clear session state
        st.session_state.user = None
        st.session_state.auth_state = "needs_login"
        
        # Clear auth cookies
        clear_auth_cookies()
        
        if is_development:
            st.write("Debug: User logged out successfully")
            
        st.success("Logged out successfully!")
        
        # Redirect to home
        st.session_state.current_page = 'home'
        
    except Exception as e:
        if is_development:
            st.error(f"Error during logout: {str(e)}")
            st.error(traceback.format_exc())

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
    """Restore authentication data from cookies"""
    try:
        if is_development:
            st.write("Debug: Attempting to restore auth from cookies")
        
        # Get tokens from cookies
        auth_token = st.session_state.get('auth_token')
        refresh_token = st.session_state.get('refresh_token')
        
        if auth_token and refresh_token:
            if is_development:
                st.write("Debug: Found stored tokens, attempting to restore session")
            
            # Create a service role client for auth operations
            service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            url = os.getenv('SUPABASE_URL')
            service_client = create_client(url, service_key)
            
            # Try to set the auth and restore the session
            try:
                # Attempt to use the auth token - we can't set session with service role
                # Instead, use the token to get the user directly
                try:
                    # Get user by JWT
                    auth_user = service_client.auth.get_user(auth_token)
                    
                    if auth_user and hasattr(auth_user, 'user'):
                        st.session_state.user = auth_user.user
                        st.session_state.auth_state = "authenticated"
                        if is_development:
                            st.write(f"Debug: Successfully restored auth for user: {auth_user.user.email}")
                        return True
                    else:
                        if is_development:
                            st.write("Debug: Failed to restore user from auth token")
                        
                        # Try to refresh the token
                        try:
                            if is_development:
                                st.write("Debug: Attempting to refresh token")
                                
                            # Create a client with the refresh token
                            client = create_client(url, service_key)
                            client.auth.set_session(auth_token, refresh_token)
                            new_session = client.auth.refresh_session()
                            
                            if new_session:
                                st.session_state.user = new_session.user
                                save_auth_to_cookie(new_session.session)
                                st.session_state.auth_state = "authenticated"
                                if is_development:
                                    st.write(f"Debug: Successfully refreshed token for user: {new_session.user.email}")
                                return True
                        except Exception as refresh_err:
                            if is_development:
                                st.write(f"Debug: Token refresh failed: {str(refresh_err)}")
                            # Clear invalid auth data
                            clear_auth_cookies()
                            st.session_state.auth_state = "needs_login"
                except Exception as auth_err:
                    if is_development:
                        st.write(f"Debug: Error getting user from token: {str(auth_err)}")
                    # Clear the invalid auth data
                    clear_auth_cookies()
                    st.session_state.auth_state = "needs_login"
            except Exception as session_err:
                if is_development:
                    st.write(f"Debug: Error setting session from tokens: {str(session_err)}")
                # Clear the invalid auth data
                clear_auth_cookies()
                st.session_state.auth_state = "needs_login"
        else:
            if is_development:
                st.write("Debug: No stored auth tokens found")
            st.session_state.auth_state = "needs_login"
            
        return False
    except Exception as e:
        if is_development:
            st.error(f"Error restoring auth from cookies: {str(e)}")
            st.error(traceback.format_exc())
        st.session_state.auth_state = "needs_login"
        return False

def get_current_user():
    """Get the current authenticated user"""
    try:
        if st.session_state.get('user'):
            # Create a service role client for auth operations
            service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
            url = os.getenv('SUPABASE_URL')
            service_client = create_client(url, service_key)
            
            # Verify token validity by making a simple query
            try:
                # Test with a simple query to verify user exists
                user_id = st.session_state.user.id
                test = service_client.table('users').select('id').eq('id', user_id).limit(1).execute()
                
                if test.data:
                    # User exists in database
                    return st.session_state.user
                else:
                    # User not found, try to refresh token
                    if is_development:
                        st.write("Debug: User not found in database, attempting to refresh token")
                    refresh_token = st.session_state.get('refresh_token')
                    auth_token = st.session_state.get('auth_token')
                    
                    if refresh_token and auth_token:
                        try:
                            # Create a client with the refresh token
                            temp_client = create_client(url, service_key)
                            temp_client.auth.set_session(auth_token, refresh_token)
                            new_session = temp_client.auth.refresh_session()
                            
                            if new_session:
                                st.session_state.user = new_session.user
                                save_auth_to_cookie(new_session.session)
                                if is_development:
                                    st.write("Debug: Token refreshed successfully")
                                return st.session_state.user
                        except Exception as refresh_error:
                            if is_development:
                                st.write(f"Debug: Token refresh failed: {str(refresh_error)}")
                            # Clear invalid auth data
                            st.session_state.user = None
                            clear_auth_cookies()
                    else:
                        # No refresh token, clear invalid auth
                        st.session_state.user = None
                        clear_auth_cookies()
            except Exception as token_check_error:
                if is_development:
                    st.write(f"Debug: Token check error: {str(token_check_error)}")
                # Return user anyway but mark auth_state for refresh on next cycle
                st.session_state.auth_state = "token_error"
                return st.session_state.user
                
        return None
    except Exception as e:
        if is_development:
            st.error(f"Error getting current user: {str(e)}")
            st.error(traceback.format_exc())
        return None

def handle_auth_state():
    """Handle the authentication state of the user."""
    try:
        if is_development:
            st.write("Debug: Handling auth state")
        
        # Get the current auth state
        auth_state = st.session_state.get('auth_state')
        
        if is_development:
            st.write(f"Debug: Current auth state: {auth_state}")
        
        # If auth_state is token_error, try to refresh
        if auth_state == "token_error":
            if is_development:
                st.write("Debug: Attempting to fix token error")
            
            refresh_token = st.session_state.get('refresh_token')
            auth_token = st.session_state.get('auth_token')
            
            if refresh_token and auth_token:
                try:
                    # Create a service role client for auth operations
                    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
                    url = os.getenv('SUPABASE_URL')
                    
                    # Create a temporary client with the user's tokens
                    temp_client = create_client(url, service_key)
                    temp_client.auth.set_session(auth_token, refresh_token)
                    
                    # Try to refresh the session
                    new_session = temp_client.auth.refresh_session()
                    
                    if new_session:
                        st.session_state.user = new_session.user
                        save_auth_to_cookie(new_session.session)
                        st.session_state.auth_state = "authenticated"
                        if is_development:
                            st.write("Debug: Token refreshed successfully")
                        return "authenticated"
                except Exception as refresh_error:
                    if is_development:
                        st.write(f"Debug: Token refresh failed: {str(refresh_error)}")
                    st.session_state.user = None
                    clear_auth_cookies()
                    st.session_state.auth_state = "needs_login"
                    return "needs_login"
            else:
                # No refresh token or auth token, mark as needing login
                st.session_state.auth_state = "needs_login"
                return "needs_login"
        
        # If we don't have an auth state, we need to check if the user is logged in
        if auth_state is None:
            if is_development:
                st.write("Debug: No auth state found, checking if user is logged in")
            
            user = get_current_user()
            
            if user:
                if is_development:
                    st.write("Debug: User found in session state")
                st.session_state.auth_state = "authenticated"
                return "authenticated"
            else:
                if is_development:
                    st.write("Debug: No user found in session state")
                st.session_state.auth_state = "needs_login"
                return "needs_login"
        
        return auth_state
    except Exception as e:
        if is_development:
            st.error(f"Error handling auth state: {str(e)}")
            st.error(traceback.format_exc())
        return None 