import streamlit as st
import io
from utils.translation_utils import t
from services.data_service import update_item, add_item
from utils.image_utils import generate_sales_photo
from PIL import Image

def render_edit_modal(rerun_callback=None):
    """Render the edit item modal when triggered"""
    if st.session_state.get('show_edit_modal') and st.session_state.get('editing_item'):
        with st.form("edit_item_form"):
            item = st.session_state.editing_item
            
            # Wrap the entire form in the compact-form class
            st.markdown('<div class="compact-form">', unsafe_allow_html=True)
            
            # Name field
            name = st.text_input(t('item_name'), value=item['name'])
            
            # Price fields in a row
            col1, col2 = st.columns(2)
            with col1:
                price_usd = st.number_input("USD", min_value=0, value=int(item.get('price_usd', 0) or 0))
            with col2:
                price_local = st.number_input("LOCAL", min_value=0, value=int(item.get('price_local', 0) or 0))
            
            # Status and sold_to in a row
            col1, col2 = st.columns([3, 2])
            with col1:
                status_options = {
                    'available': ('🏷️ ' + t('status_available'), 'status-available'),
                    'paid_pending_pickup': ('💰 ' + t('status_paid'), 'status-paid'),
                    'claimed_not_paid': ('⏳ ' + t('status_claimed'), 'status-claimed'),
                    'paid_picked_up': ('✅ ' + t('status_complete'), 'status-complete')
                }
                
                current_status = item.get('sale_status')
                selected_status = current_status if current_status in status_options else 'available'
                
                status_display = {text: key for key, (text, _) in status_options.items()}
                selected_status_text = next(text for key, (text, _) in status_options.items() if key == selected_status)
                
                new_status_text = st.radio(
                    "Status",
                    options=list(status_display.keys()),
                    index=list(status_display.keys()).index(selected_status_text),
                    horizontal=True,
                    label_visibility="collapsed"
                )
                selected_status = status_display[new_status_text]
            
            with col2:
                sold_to = ""
                if selected_status != 'available':
                    sold_to = st.text_input("Sold to", value=item.get('sold_to', ''), label_visibility="collapsed", placeholder="Sold to")
            
            # Optional image upload
            image = st.file_uploader(t('upload_new_image'), type=["jpg", "jpeg", "png"])
            
            # Add buttons in a row at the bottom
            col1, col2 = st.columns([1, 1])
            with col1:
                submit = st.form_submit_button(t('save_changes'))
                if submit:
                    item_data = {
                        "name": name,
                        "price_usd": int(price_usd) if price_usd > 0 else None,
                        "price_local": int(price_local) if price_local > 0 else None,
                        "sale_status": selected_status,
                        "is_sold": selected_status == 'paid_picked_up',
                        "user_id": st.session_state.user.id
                    }
                    if selected_status != 'available' and sold_to:
                        item_data['sold_to'] = sold_to
                    updated_item = update_item(item['id'], item_data, image)
                    if updated_item:
                        st.success(t('item_updated'))
                        st.session_state.show_edit_modal = False
                        st.session_state.editing_item = None
                        # Clear the cache to force reload of items
                        st.cache_data.clear()
                        if rerun_callback:
                            rerun_callback()
            with col2:
                if st.form_submit_button(t('cancel')):
                    st.session_state.show_edit_modal = False
                    st.session_state.editing_item = None
                    if rerun_callback:
                        rerun_callback()
            
            st.markdown('</div>', unsafe_allow_html=True)

def render_item_grid(items, enable_edit=True, rerun_callback=None):
    """Render a grid of items"""
    if not items:
        st.info(t('no_items_found', status=st.session_state.current_page.replace('_', ' ')))
        return
        
    # Create a grid layout for items
    cols = st.columns(3)
    for i, item in enumerate(items):
        with cols[i % 3]:
            if item.get('image_url'):
                # Try to use pre-generated sales photo URL
                if item.get('sales_overlay_url'):
                    st.image(item['sales_overlay_url'], caption=item['name'])
                else:
                    # Generate and cache if needed
                    sales_photo = generate_sales_photo(
                        item['image_url'],
                        item.get('price_usd'),
                        item.get('price_local'),
                        item['name'],
                        "overlay",
                        item['id']
                    )
                    if sales_photo:
                        st.image(io.BytesIO(sales_photo), caption=item['name'])
            else:
                st.image("https://via.placeholder.com/200x200?text=No+Image", caption=item['name'])
            
            # Show prices
            if item.get('price_usd') and item.get('price_local'):
                st.write(f"${item['price_usd']} USD / {item['price_local']} Moneda Local")
            elif item.get('price_usd'):
                st.write(f"${item['price_usd']} USD")
            elif item.get('price_local'):
                st.write(f"{item['price_local']} Moneda Local")
            
            # Show status with color coding
            status_info = {
                'paid_pending_pickup': ('💰 ' + t('status_paid'), 'status-paid'),
                'claimed_not_paid': ('⏳ ' + t('status_claimed'), 'status-claimed'),
                'paid_picked_up': ('✅ ' + t('status_complete'), 'status-complete'),
                None: ('🏷️ ' + t('status_available'), 'status-available')
            }
            
            status_text, status_class = status_info.get(item.get('sale_status'), ('🏷️ ' + t('status_available'), 'status-available'))
            
            # Create a row for status, sold-to, and edit button
            st.markdown('<div class="tag-container">', unsafe_allow_html=True)
            # Adjusted column widths to give more space to the edit button
            col1, col2, col3 = st.columns([1.5, 1.5, 1])
            with col1:
                st.markdown(f'<div class="status-tag {status_class}">{status_text}</div>', unsafe_allow_html=True)
            
            with col2:
                # Show sold to name if status is not available
                if item.get('sale_status') != 'available' and item.get('sold_to'):
                    st.markdown(f'<div class="status-tag status-sold-to">👤 {item["sold_to"]}</div>', unsafe_allow_html=True)
            
            with col3:
                if enable_edit and st.button(t('edit'), key=f"edit_{item['id']}", type="secondary", use_container_width=True):
                    st.session_state.editing_item = item
                    st.session_state.show_edit_modal = True
                    if rerun_callback:
                        rerun_callback()
            st.markdown('</div>', unsafe_allow_html=True)

def render_add_item_form(rerun_callback=None):
    """Render the add item form"""
    from services.data_service import add_item
    
    st.title(t('add_item'))
    
    with st.form("add_item_form"):
        # Wrap the entire form in the compact-form class
        st.markdown('<div class="compact-form">', unsafe_allow_html=True)
        
        # Name field
        name = st.text_input(t('item_name'))
        
        # Price fields in a row
        col1, col2 = st.columns(2)
        with col1:
            price_usd = st.number_input("USD", min_value=0, value=0)
        with col2:
            price_local = st.number_input("LOCAL", min_value=0, value=0)
        
        # Status and sold_to in a row
        col1, col2 = st.columns([3, 2])
        with col1:
            status_options = {
                'available': ('🏷️ ' + t('status_available'), 'status-available'),
                'paid_pending_pickup': ('💰 ' + t('status_paid'), 'status-paid'),
                'claimed_not_paid': ('⏳ ' + t('status_claimed'), 'status-claimed'),
                'paid_picked_up': ('✅ ' + t('status_complete'), 'status-complete')
            }
            
            status_display = {text: key for key, (text, _) in status_options.items()}
            
            new_status_text = st.radio(
                "Status",
                options=list(status_display.keys()),
                horizontal=True,
                label_visibility="collapsed"
            )
            selected_status = status_display[new_status_text]
        
        with col2:
            sold_to = ""
            if selected_status != 'available':
                sold_to = st.text_input("Sold to", label_visibility="collapsed", placeholder="Sold to")
        
        # Optional image upload
        image = st.file_uploader(t('upload_image'), type=["jpg", "jpeg", "png"])
        
        submit = st.form_submit_button(t('add_item_button'))
        if submit:
            if not name:
                st.error(t('fill_required_fields'))
            else:
                item_data = {
                    "name": name,
                    "price_usd": int(price_usd) if price_usd > 0 else None,
                    "price_local": int(price_local) if price_local > 0 else None,
                    "user_id": st.session_state.user.id,
                    "sale_status": selected_status,
                    "is_sold": selected_status == 'paid_picked_up'
                }
                
                # Ensure at least one price is set
                if price_usd <= 0 and price_local <= 0:
                    st.error("Please enter at least one price (USD or Local)")
                    return
                
                if selected_status != 'available' and sold_to:
                    item_data['sold_to'] = sold_to
                
                new_item = add_item(item_data, image)
                if new_item:
                    st.success(t('item_added'))
                    # Clear the cache to force reload of items
                    st.cache_data.clear()
                    # Switch to the available items view
                    st.session_state.current_page = 'available'
                    if rerun_callback:
                        rerun_callback()
        
        st.markdown('</div>', unsafe_allow_html=True)

def render_sold_to_view(items):
    """Render items grouped by sold_to"""
    
    # Group items by sold_to
    sold_items = [item for item in items if item.get('sold_to')]
    if sold_items:
        # Group by sold_to
        sold_to_groups = {}
        for item in sold_items:
            buyer = item.get('sold_to', 'Unknown')
            if buyer not in sold_to_groups:
                sold_to_groups[buyer] = []
            sold_to_groups[buyer].append(item)
        
        # Display each group
        for buyer, buyer_items in sold_to_groups.items():
            st.subheader(f"👤 {buyer}")
            render_item_grid(buyer_items)
    else:
        st.info(t('no_sold_items')) 