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
    
    # Get additional user details if needed for debugging
    if is_development:
        st.write(f"User ID: {st.session_state.user.id if st.session_state.user else None}")
        st.write(f"User email: {st.session_state.user.email if st.session_state.user else None}")
        
        try:
            user_details = get_user_details_safely(st.session_state.user.id)
            st.write(f"User details retrieved: {user_details}")
        except Exception as e:
            st.error(f"Error getting user info: {str(e)}")
            st.error(traceback.format_exc())
    
    # Get all public links for the current user
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
    
    # Create a new public link form
    with st.form("create_link_form"):
        name = st.text_input(t('link_name'), value="My Items Collection")
        submit = st.form_submit_button(t('create_new_link'))
        if submit:
            link = create_public_link(name)
            if link:
                st.success(t('link_created'))
                st.rerun()  # Refresh the page
    
    # Display existing links or offer to create one
    if not links:
        st.info(t('no_public_links'))
        
        # Add a button to create one outside the form
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
    
    # Display active links
    if active_links:
        st.header(t('active_links'))
        for link in active_links:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 3, 1, 1])
                
                with col1:
                    st.markdown(f"**{link['name']}**")
                    
                with col2:
                    app_url = st.session_state.base_url
                    full_link = f"{app_url}?code={link['link_code']}"
                    st.markdown(f"[{full_link}]({full_link})")
                    st.caption(f"{t('created')}: {link['created_at'][:10]}")
                    
                with col3:
                    if st.button(t('copy_link'), key=f"copy_{link['id']}"):
                        # Create a JS command to copy the link
                        copy_code = f"""
                        <script>
                        const el = document.createElement('textarea');
                        el.value = '{full_link}';
                        document.body.appendChild(el);
                        el.select();
                        document.execCommand('copy');
                        document.body.removeChild(el);
                        </script>
                        """
                        st.markdown(copy_code, unsafe_allow_html=True)
                        st.success("Link copied!")
                    
                with col4:
                    if st.button(t('deactivate'), key=f"deactivate_{link['id']}"):
                        update_public_link(link['id'], {'is_active': False})
                        st.success(t('link_deactivated'))
                        st.rerun()
                
                st.markdown("---")
                
                # Add toggle UI in a more detailed view for the first active link
                if link == active_links[0]:
                    # Make the URL copyable
                    st.text_input("Share this link:", full_link, label_visibility="visible", key=f"share_input_{link['id']}")
                    
                    # Show status
                    status_color = ":green"
                    st.write(f"{status_color}[●] Status: Active")
    else:
        st.info(t('no_active_links'))
    
    # Display inactive links
    if inactive_links:
        st.header(t('inactive_links'))
        for link in inactive_links:
            with st.container():
                col1, col2, col3, col4 = st.columns([2, 3, 1, 1])
                
                with col1:
                    st.markdown(f"**{link['name']}**")
                    
                with col2:
                    st.caption(f"{t('link_code')}: {link['link_code']}")
                    st.caption(f"{t('created')}: {link['created_at'][:10]}")
                    
                with col3:
                    if st.button(t('activate'), key=f"activate_{link['id']}"):
                        update_public_link(link['id'], {'is_active': True})
                        st.success(t('link_activated'))
                        st.rerun()
                    
                with col4:
                    if st.button(t('delete'), key=f"delete_{link['id']}"):
                        delete_public_link(link['id'])
                        st.success(t('link_deleted'))
                        st.rerun()
                
                st.markdown("---")
                
                # Add toggle UI in a more detailed view for the first inactive link
                if link == inactive_links[0]:
                    # Show full URL
                    app_url = st.session_state.base_url
                    full_link = f"{app_url}?code={link['link_code']}"
                    st.text_input("Share this link:", full_link, label_visibility="visible", key=f"share_input_{link['id']}")
                    
                    # Show status
                    status_color = ":red"
                    st.write(f"{status_color}[●] Status: Inactive")
                    
                    # Add a toggle to activate the link
                    new_status = st.toggle("Enable this link", value=False, key=f"toggle_{link['id']}")
                    
                    # If toggle state changed, update the link status
                    if new_status != False:
                        try:
                            if update_public_link(link['id'], {'is_active': new_status}):
                                st.success("Link status updated!")
                                st.rerun()
                        except Exception as e:
                            if is_development:
                                st.error(f"Error updating link status: {str(e)}")
                                st.error(traceback.format_exc())
                            st.error("Could not update link status. Please try again.")
    else:
        st.info(t('no_inactive_links'))
    
    # Add help text
    st.markdown("---")
    st.markdown("**Note:** When your link is active, anyone with the URL can view your available items.")
    
    # If there are multiple links (from previous version), show a message
    if len(links) > 1:
        st.warning("Multiple public links found. Only the first one is being used.") 