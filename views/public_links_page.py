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
    
    # Create service role client for database operations
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    url = os.getenv('SUPABASE_URL')
    service_client = create_client(url, service_key)
    
    # Get existing public links with error handling
    try:
        links = get_user_public_links()
        
        if is_development:
            st.write(f"Found {len(links)} public links")
    except Exception as e:
        if is_development:
            st.error(f"Error fetching public links: {str(e)}")
            st.error(traceback.format_exc())
        links = []
        st.warning("Could not load your public links. Please try refreshing the page.")
    
    # Create a new public link
    with st.form("create_link_form"):
        name = st.text_input(t('link_name'), value="My Items Collection")
        submit = st.form_submit_button(t('create_new_link'))
        if submit:
            link = create_public_link(name)
            if link:
                st.success(t('link_created'))
                st.rerun()  # Refresh the page
    
    # Display existing links
    if not links:
        st.info(t('no_public_links'))
        
        # Create a simple button to generate a link
        if st.button("Create Public Link", use_container_width=True):
            # Create a link with the user's name
            try:
                user_info = service_client.table('users')\
                    .select('first_name')\
                    .eq('id', st.session_state.user.id)\
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
        return
        
    # Split into active and inactive links
    active_links = [link for link in links if link.get('is_active')]
    inactive_links = [link for link in links if not link.get('is_active')]
    
    # Get the base URL for public links
    base_url = st.session_state.get('base_url', 'http://localhost:8501')
    
    if active_links:
        st.header(t('active_links'))
        for link in active_links:
            with st.container():
                col1, col2, col3 = st.columns([2, 3, 1])
                
                with col1:
                    st.markdown(f"**{link['name']}**")
                    st.caption(f"{t('created')}: {link['created_at'][:10]}")
                    
                with col2:
                    # Display link only in a code block with built-in copy button
                    full_link = f"{base_url}?code={link['link_code']}"
                    st.code(full_link, language=None)
                    
                with col3:
                    if st.button(t('deactivate'), key=f"deactivate_{link['id']}"):
                        update_public_link(link['id'], {'is_active': False})
                        st.success(t('link_deactivated'))
                        st.rerun()
                
                st.markdown("---")
    else:
        st.info(t('no_active_links'))
    
    if inactive_links:
        st.header(t('inactive_links'))
        for link in inactive_links:
            with st.container():
                col1, col2, col3 = st.columns([2, 3, 1])
                
                with col1:
                    st.markdown(f"**{link['name']}**")
                    st.caption(f"{t('created')}: {link['created_at'][:10]}")
                    
                with col2:
                    # Show link code but in a code block for consistency
                    full_link = f"{base_url}?code={link['link_code']}"
                    st.code(full_link, language=None)
                    
                with col3:
                    col3_1, col3_2 = st.columns(2)
                    with col3_1:
                        if st.button(t('activate'), key=f"activate_{link['id']}"):
                            update_public_link(link['id'], {'is_active': True})
                            st.success(t('link_activated'))
                            st.rerun()
                    
                    with col3_2:
                        if st.button(t('delete'), key=f"delete_{link['id']}"):
                            delete_public_link(link['id'])
                            st.success(t('link_deleted'))
                            st.rerun()
                
                st.markdown("---")
    
    # Display user info and guidance
    st.markdown("---")
    st.markdown("**Note:** When your link is active, anyone with the URL can view your available items.")
    
    # Display warning if multiple links (from previous version)
    if len(links) > 1:
        st.warning("You have multiple public links. All are shown above.")
        
    # Development mode information
    if is_development:
        st.markdown("---")
        st.subheader("Development Information")
        st.write(f"User ID: {st.session_state.user.id if st.session_state.user else None}")
        st.write(f"User email: {st.session_state.user.email if st.session_state.user else None}")
        
        try:
            if st.session_state.user and hasattr(st.session_state.user, 'id'):
                user_details = get_user_details_safely(st.session_state.user.id)
                st.write(f"User details retrieved: {user_details}")
        except Exception as e:
            st.error(f"Error getting user info: {str(e)}")
            st.error(traceback.format_exc()) 