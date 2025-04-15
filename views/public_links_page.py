import os
import streamlit as st
import traceback
from supabase import create_client
from services.data_service import get_user_details_safely, get_user_public_links, create_public_link, update_public_link, delete_public_link
from utils.translation_utils import t

# Set development mode flag
is_development = os.getenv('ENVIRONMENT', '').lower() == 'development'

def render_public_links_page():
    st.title(t('public_links'))
    st.markdown(t('public_links_desc'))
    
    # Get user info from session
    user = st.session_state.user
    
    if is_development:
        st.write(f"User ID: {user.id if user else None}")
        st.write(f"User email: {user.email if user else None}")
    
    # Get additional user details from the database
    try:
        if not user or not hasattr(user, 'id'):
            st.error("User information is missing or invalid. Please try logging in again.")
            return
        
        user_details = get_user_details_safely(user.id)
        
        if is_development:
            st.write(f"User details retrieved: {user_details}")
        
        if not user_details:
            st.warning("User details could not be found. Some features may not be available.")
            return

    except Exception as e:
        if is_development:
            st.error(f"Error getting user info: {str(e)}")
            st.error(traceback.format_exc())
        st.error("Could not load user details. Please try again later.")
        return
    
    # Get the base URL for public links
    base_url = st.session_state.get('base_url', 'http://localhost:8501')
    
    # Get existing public links with error handling
    try:
        public_links = get_user_public_links()
        
        if is_development:
            st.write(f"Found {len(public_links)} public links")
    except Exception as e:
        if is_development:
            st.error(f"Error fetching public links: {str(e)}")
            st.error(traceback.format_exc())
        public_links = []
        st.warning("Could not load your public links. Please try refreshing the page.")
    
    # Check if the user already has a public link
    if not public_links:
        # User doesn't have a link yet, offer to create one
        st.info("You haven't created a public link yet. Create one to share your available items.")
        
        # Create a simple button to generate a link
        if st.button("Create Public Link", use_container_width=True):
            # Create a link with the user's name
            try:
                user_info = st.session_state.supabase.table('users')\
                    .select('first_name')\
                    .eq('id', user.id)\
                    .execute()
                
                first_name = 'User'  # Default value
                if user_info and hasattr(user_info, 'data') and user_info.data:
                    first_name = user_info.data[0].get('first_name', 'User')
                
                link_name = f"{first_name}'s Items for Sale"
                new_link = create_public_link(link_name)
                if new_link:
                    st.success("Your public link has been created!")
                    st.rerun()
            except Exception as e:
                if is_development:
                    st.error(f"Error creating public link: {str(e)}")
                    st.error(traceback.format_exc())
                st.error("Could not create public link. Please try again.")
    else:
        # User already has at least one link, show the first (or only) one
        link = public_links[0]
        
        # Create a card-like container for the link info
        with st.container():
            # Display the link details
            st.subheader("Your Public Link")
            
            # Full URL to share - use query parameter
            full_url = f"{base_url}?code={link['link_code']}"
            
            # Make the URL copyable
            st.text_input("Share this link:", full_url, label_visibility="visible")
            
            # Show link status
            is_active = link.get('is_active', False)
            status_color = ":green" if is_active else ":red"
            
            # Display status with colored circle
            st.write(f"{status_color}[●] Status: {'Active' if is_active else 'Inactive'}")
            
            # Add a toggle to activate/deactivate the link
            new_status = st.toggle("Enable this link", value=is_active)
            
            # If toggle state changed, update the link status
            if new_status != is_active:
                try:
                    if update_public_link(link['id'], {'is_active': new_status}):
                        st.success("Link status updated!")
                        st.rerun()
                except Exception as e:
                    if is_development:
                        st.error(f"Error updating link status: {str(e)}")
                        st.error(traceback.format_exc())
                    st.error("Could not update link status. Please try again.")
        
        # Add help text
        st.markdown("---")
        st.markdown("**Note:** When your link is active, anyone with the URL can view your available items.")
        
        # If there are multiple links (from previous version), show a message
        if len(public_links) > 1:
            st.warning("Multiple public links found. Only the first one is being used.") 