import os
import streamlit as st
import traceback
from utils.translation_utils import t
from services.data_service import load_items

# Set development mode flag
is_development = os.getenv('ENVIRONMENT', '').lower() == 'development'

def render_home_page():
    """Render the home page with a welcome message and summary of items."""
    try:
        # Get user info from session
        user = st.session_state.user
        
        if is_development:
            st.write(f"Debug: Rendering home page for user: {user.id if user else None}")
        
        # Get user's first name from the database
        try:
            user_info = st.session_state.supabase.table('users')\
                .select('first_name')\
                .eq('id', user.id)\
                .execute()
            
            first_name = 'User'  # Default value
            if user_info and hasattr(user_info, 'data') and user_info.data:
                first_name = user_info.data[0].get('first_name', 'User')
        except Exception as e:
            if is_development:
                st.error(f"Error getting user info: {str(e)}")
                st.error(traceback.format_exc())
            first_name = 'User'
        
        # Display welcome message
        st.markdown(f'<h1 class="greeting">Welcome back, {first_name}!</h1>', unsafe_allow_html=True)
        
        # Load items
        try:
            items = load_items()
            
            if is_development:
                st.write(f"Debug: Loaded {len(items)} items")
            
            # Calculate summary statistics
            total_items = len(items)
            available_items = len([item for item in items if item.get('status') == 'available'])
            paid_items = len([item for item in items if item.get('status') == 'paid_ready'])
            claimed_items = len([item for item in items if item.get('status') == 'claimed'])
            complete_items = len([item for item in items if item.get('status') == 'complete'])
            
            # Display summary cards
            col1, col2, col3, col4, col5 = st.columns(5)
            
            with col1:
                st.metric("Total Items", total_items)
            with col2:
                st.metric("Available", available_items)
            with col3:
                st.metric("Paid", paid_items)
            with col4:
                st.metric("Claimed", claimed_items)
            with col5:
                st.metric("Complete", complete_items)
            
            # Add a separator
            st.markdown("---")
            
            # Quick actions section
            st.subheader("Quick Actions")
            
            # Create columns for quick action buttons
            action_col1, action_col2, action_col3 = st.columns(3)
            
            with action_col1:
                if st.button("➕ Add New Item", use_container_width=True):
                    st.session_state.current_page = "add"
                    st.rerun()
            
            with action_col2:
                if st.button("📸 Generate Photos", use_container_width=True):
                    st.session_state.current_page = "photos"
                    st.rerun()
            
            with action_col3:
                if st.button("🔗 Create Public Link", use_container_width=True):
                    st.session_state.current_page = "public_links"
                    st.rerun()
            
            # Add a separator
            st.markdown("---")
            
            # Recent activity section
            st.subheader("Recent Activity")
            
            # Get recent items (last 5)
            recent_items = sorted(items, key=lambda x: x.get('created_at', ''), reverse=True)[:5]
            
            if recent_items:
                for item in recent_items:
                    with st.container():
                        col1, col2 = st.columns([1, 4])
                        with col1:
                            if item.get('image_url'):
                                st.image(item['image_url'], width=100)
                            else:
                                st.write("No image")
                        with col2:
                            st.write(f"**{item.get('name', 'Unnamed Item')}**")
                            st.write(f"Status: {item.get('status', 'Unknown')}")
                            st.write(f"Price: ${item.get('price_usd', 0):.2f}")
            
            else:
                st.info("No recent activity to show. Add your first item to get started!")
                
        except Exception as e:
            if is_development:
                st.error(f"Error loading items: {str(e)}")
                st.error(traceback.format_exc())
            st.error("Could not load your items. Please try refreshing the page.")
            
    except Exception as e:
        if is_development:
            st.error(f"Error rendering home page: {str(e)}")
            st.error(traceback.format_exc())
        st.error("An error occurred while loading this page. Please try again or contact support.") 