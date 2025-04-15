import streamlit as st
import traceback
from utils.translation_utils import t
from services.data_service import update_user_whatsapp

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
        
        # If the user has pending WhatsApp info to update, do it now
        if 'whatsapp_info' in st.session_state:
            whatsapp_info = st.session_state.whatsapp_info
            update_user_whatsapp(
                whatsapp_info['phone'], 
                whatsapp_info['share']
            )
            # Remove the temporary data
            del st.session_state.whatsapp_info
        
        st.success("Login successful!")
        return True
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
            
        st.write("Attempting to sign up...")
        
        try:
            auth = st.session_state.supabase.auth.sign_up({
                "email": email,
                "password": password
            })
            
            if auth.user:
                # Create the user record in our users table with name fields
                user_data = {
                    'id': auth.user.id,
                    'email': auth.user.email,
                    'first_name': first_name,
                    'last_name': last_name,
                    'role': 'user'
                }
                
                # Add WhatsApp information if available
                if whatsapp_phone:
                    user_data['whatsapp_phone'] = whatsapp_phone
                    user_data['share_whatsapp_for_items'] = share_whatsapp
                
                try:
                    st.session_state.supabase.table('users').insert(user_data).execute()
                except Exception as db_error:
                    # Check if this is a duplicate key error
                    error_str = str(db_error)
                    if "duplicate key" in error_str and "users_pkey" in error_str:
                        st.error(t('account_already_exists'))
                        # Try to clean up the auth user since we couldn't create the profile
                        try:
                            # This might not always work depending on permissions
                            st.session_state.supabase.auth.admin.delete_user(auth.user.id)
                        except:
                            pass
                        return False
                    else:
                        # Re-raise if it's a different error
                        raise
                
            return True
            
        except Exception as auth_error:
            # Check for Supabase auth errors that indicate duplicate email
            error_str = str(auth_error)
            if "User already registered" in error_str or "already exists" in error_str:
                st.error(t('account_already_exists'))
                return False
            else:
                # Re-raise if it's a different error
                raise
                
    except Exception as e:
        # Generic error handling
        st.error(t('signup_failed'))
        if st.session_state.get('debug_mode', False):
            st.error(f"Error details: {str(e)}")
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