import streamlit as st
from services.data_service import get_user_public_links, create_public_link, update_public_link, delete_public_link
from utils.translation_utils import t

def render_public_links_page():
    st.title(t('public_links'))
    st.markdown(t('public_links_desc'))
    
    # Get the base URL for public links
    # This assumes the app is deployed with a public URL
    # For local development, we'll use a placeholder
    base_url = st.session_state.get('base_url', 'http://localhost:8501')
    
    # Get user's first name
    user_info = st.session_state.supabase.table('users')\
        .select('first_name')\
        .eq('id', st.session_state.user.id)\
        .execute()
    
    first_name = user_info.data[0]['first_name'] if user_info.data else 'User'
    
    # Set default link name with user's first name
    default_link_name = f"{first_name}'s Available Items"
    
    # Add a button to create a new public link
    col1, col2 = st.columns([3, 1])
    
    with col1:
        new_link_name = st.text_input(t('link_name'), value=default_link_name)
    
    with col2:
        if st.button(t('create_new_link'), use_container_width=True):
            if new_link_name:
                new_link = create_public_link(new_link_name)
                if new_link:
                    st.success(t('link_created'))
                    st.rerun()
    
    st.markdown("---")
    
    # Display existing links
    public_links = get_user_public_links()
    
    if not public_links:
        st.info(t('no_public_links'))
    else:
        # Create tabs for active and inactive links
        active_links = [link for link in public_links if link.get('is_active')]
        inactive_links = [link for link in public_links if not link.get('is_active')]
        
        tab1, tab2 = st.tabs([t('active_links'), t('inactive_links')])
        
        with tab1:
            if not active_links:
                st.info(t('no_active_links'))
            else:
                for link in active_links:
                    display_link_card(link, base_url, is_active=True)
        
        with tab2:
            if not inactive_links:
                st.info(t('no_inactive_links'))
            else:
                for link in inactive_links:
                    display_link_card(link, base_url, is_active=False)

def display_link_card(link, base_url, is_active=True):
    with st.container():
        st.markdown("---")
        col1, col2, col3 = st.columns([3, 2, 1])
        
        # Column 1: Link details
        with col1:
            st.subheader(link.get('name', t('available_items')))
            st.caption(f"{t('created')}: {link.get('created_at', '')[:10]}")
            
            # Full URL to share - use query parameter instead of path segment
            full_url = f"{base_url}?code={link['link_code']}"
            
            # Make the URL copyable from the display
            st.text_input("", full_url, key=f"url_{link['id']}", label_visibility="collapsed")
        
        # Column 2: Statistics & info
        with col2:
            st.markdown(f"**{t('link_code')}:** {link['link_code']}")
            # In a future enhancement, you could add view statistics here
            
        # Column 3: Actions
        with col3:
            # Toggle active status
            if is_active:
                if st.button(t('deactivate'), key=f"deactivate_{link['id']}", use_container_width=True):
                    if update_public_link(link['id'], {'is_active': False}):
                        st.success(t('link_deactivated'))
                        st.rerun()
            else:
                if st.button(t('activate'), key=f"activate_{link['id']}", use_container_width=True):
                    if update_public_link(link['id'], {'is_active': True}):
                        st.success(t('link_activated'))
                        st.rerun()
            
            # Delete link
            if st.button(t('delete'), key=f"delete_{link['id']}", use_container_width=True):
                if delete_public_link(link['id']):
                    st.success(t('link_deleted'))
                    st.rerun()
            
            # Copy link button using a more reliable approach
            if st.button(t('copy_link'), key=f"copy_{link['id']}", use_container_width=True):
                st.success(f"{t('copy_link')}!")
                # Note: The URL is already copyable from the text_input above 