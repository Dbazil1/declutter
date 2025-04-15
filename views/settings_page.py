import os
import streamlit as st
import traceback
import time
from supabase import create_client
from services.data_service import update_user_whatsapp, get_user_details_safely
from utils.translation_utils import t

def render_settings_page():
    st.title(t("settings"))
    
    # Get user info from session
    user = st.session_state.user
    
    # Debug output in development mode - only show if explicitly set to 'development'
    is_development = os.getenv('ENVIRONMENT', '').lower() == 'development'
    
    if is_development:
        st.write(f"User ID: {user.id if user else None}")
        st.write(f"User email: {user.email if user else None}")
    
    # Get additional user details from the database using our safe function
    try:
        if not user or not hasattr(user, 'id'):
            st.error("User information is missing or invalid. Please try logging in again.")
            user_details = {'first_name': '', 'last_name': ''}
        else:
            # Use our new safer function that tries multiple methods
            user_details = get_user_details_safely(user.id)
            
            if is_development:
                st.write(f"User details retrieved: {user_details}")
            
            if not user_details:
                st.warning("User details could not be found. Some settings may not be available.")
                
                # Try to create the user record if it doesn't exist
                try:
                    if is_development:
                        st.info("Attempting to create user record...")
                    
                    # Extract metadata from user object if available
                    metadata = user.user_metadata if hasattr(user, 'user_metadata') else {}
                    first_name = metadata.get('first_name', user.email.split('@')[0] if user.email else '')
                    last_name = metadata.get('last_name', '')
                    
                    # Create user record with service role client
                    from services.data_service import check_user_details
                    
                    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
                    url = os.getenv("SUPABASE_URL")
                    client = create_client(url, service_key)
                    
                    response = client.table('users').insert({
                        'id': user.id,
                        'email': user.email,
                        'first_name': first_name,
                        'last_name': last_name,
                        'role': 'user'
                    }).execute()
                    
                    if is_development:
                        st.success("User record created successfully!")
                    
                    # Set default user details
                    user_details = {
                        'first_name': first_name,
                        'last_name': last_name,
                        'email': user.email,
                        'whatsapp_phone': '',
                        'share_whatsapp_for_items': False
                    }
                except Exception as create_err:
                    if is_development:
                        st.error(f"Failed to create user record: {str(create_err)}")
                        st.error(traceback.format_exc())
                    
                    # Default values as fallback
                    user_details = {
                        'first_name': user.email.split('@')[0] if user.email else '',
                        'last_name': '',
                        'email': user.email if hasattr(user, 'email') else '',
                        'whatsapp_phone': '',
                        'share_whatsapp_for_items': False
                    }
    except Exception as e:
        st.error(f"Error loading user details: {str(e)}")
        if is_development:
            st.error(traceback.format_exc())
        user_details = {'first_name': '', 'last_name': ''}
    
    # Display and edit personal information
    st.header(t('personal_info'))
    
    # Add form for updating personal information
    with st.form("personal_info_form"):
        # Default values from database
        default_first_name = user_details.get('first_name', '') if user_details else ''
        default_last_name = user_details.get('last_name', '') if user_details else ''
        
        # First and last name fields
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input(t('first_name'), value=default_first_name)
        with col2:
            last_name = st.text_input(t('last_name'), value=default_last_name)
        
        # Email (read-only)
        st.text_input(t('email'), value=user.email if user else '', disabled=True)
        
        # Submit button
        submit_personal = st.form_submit_button(t('save_personal_info'))
        
        if submit_personal:
            if first_name.strip() and last_name.strip():
                try:
                    # Use service role to update
                    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
                    url = os.getenv("SUPABASE_URL")
                    client = create_client(url, service_key)
                    
                    # Update user information
                    client.table('users')\
                        .update({
                            'first_name': first_name.strip(),
                            'last_name': last_name.strip()
                        })\
                        .eq('id', user.id)\
                        .execute()
                    st.success(t('personal_info_updated'))
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    if is_development:
                        st.error(f"Error updating profile: {str(e)}")
                        st.error(traceback.format_exc())
                    st.error(t('error_updating_profile'))
            else:
                st.error(t('enter_names'))
    
    # Add a separator
    st.markdown("---")
    
    # WhatsApp Settings Section
    st.header(t("whatsapp_settings"))
    
    # Use WhatsApp information from the user_details we already fetched
    whatsapp_phone = user_details.get('whatsapp_phone', '')
    share_whatsapp = user_details.get('share_whatsapp_for_items', False)
    
    # Display form for updating WhatsApp settings
    with st.form("whatsapp_settings_form"):
        st.markdown(t("whatsapp_explanation"))
        
        # WhatsApp number input - single field
        st.subheader(t("whatsapp_number"))
        
        # Process current phone number if it exists
        current_phone = ""
        
        if whatsapp_phone:
            current_phone = whatsapp_phone
            # Ensure it starts with '+'
            if not current_phone.startswith('+'):
                current_phone = '+' + current_phone
        
        # Single phone number input
        phone_number = st.text_input(
            t('full_phone_number'), 
            value=current_phone, 
            placeholder="+1 123-456-7890"
        )
        
        # Sharing settings
        share_whatsapp_checkbox = st.checkbox(
            t('enable_whatsapp'),
            value=share_whatsapp,
            help=t('whatsapp_explanation')
        )
        
        # Submit button
        submit = st.form_submit_button(t('save_settings'))
        
        if submit:
            if phone_number:
                # Format phone number (removing spaces and dashes)
                formatted_phone = phone_number.strip().replace("-", "").replace(" ", "")
                
                try:
                    # Use service role to update
                    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
                    url = os.getenv("SUPABASE_URL")
                    client = create_client(url, service_key)
                    
                    # Update WhatsApp information directly
                    client.table('users')\
                        .update({
                            'whatsapp_phone': formatted_phone,
                            'share_whatsapp_for_items': share_whatsapp_checkbox
                        })\
                        .eq('id', user.id)\
                        .execute()
                    
                    st.success(t('settings_updated'))
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    if is_development:
                        st.error(f"Error updating WhatsApp settings: {str(e)}")
                        st.error(traceback.format_exc())
                    st.error("Failed to update WhatsApp settings. Please try again.")
            else:
                st.warning(t('please_enter_whatsapp')) 