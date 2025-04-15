import streamlit as st
from services.data_service import update_user_whatsapp, get_user_whatsapp_info
from utils.translation_utils import t
import re

def render_settings_page():
    st.title(t("settings"))
    
    # Get user info from session
    user = st.session_state.user
    
    # Get additional user details from the database
    user_details = st.session_state.supabase.table('users')\
        .select('first_name, last_name')\
        .eq('id', user.id)\
        .execute().data[0] if user else None
    
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
                    # Update user information
                    st.session_state.supabase.table('users')\
                        .update({
                            'first_name': first_name.strip(),
                            'last_name': last_name.strip()
                        })\
                        .eq('id', user.id)\
                        .execute()
                    st.success(t('personal_info_updated'))
                    st.rerun()
                except Exception as e:
                    st.error(t('error_updating_profile'))
            else:
                st.error(t('enter_names'))
    
    # Add a separator
    st.markdown("---")
    
    # WhatsApp Settings Section
    st.header(t("whatsapp_settings"))
    
    # Get current WhatsApp information
    whatsapp_info = get_user_whatsapp_info(st.session_state.user.id)
    
    # Display form for updating WhatsApp settings
    with st.form("whatsapp_settings_form"):
        st.markdown(t("whatsapp_explanation"))
        
        # WhatsApp number input - single field
        st.subheader(t("whatsapp_number"))
        
        # Process current phone number if it exists
        current_phone = ""
        
        if whatsapp_info and whatsapp_info.get('whatsapp_phone'):
            current_phone = whatsapp_info['whatsapp_phone']
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
        share_whatsapp = st.checkbox(
            t('enable_whatsapp'),
            value=whatsapp_info.get('share_whatsapp_for_items', False) if whatsapp_info else False,
            help=t('whatsapp_explanation')
        )
        
        # Submit button
        submit = st.form_submit_button(t('save_settings'))
        
        if submit:
            if phone_number:
                # Format phone number (removing spaces and dashes)
                formatted_phone = phone_number.strip().replace("-", "").replace(" ", "")
                
                # Update WhatsApp information
                if update_user_whatsapp(formatted_phone, share_whatsapp):
                    st.success(t('settings_updated'))
                    st.rerun()
            else:
                st.warning(t('please_enter_whatsapp')) 