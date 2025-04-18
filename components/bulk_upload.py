import streamlit as st
import pandas as pd
from PIL import Image
import io
from services.data_service import add_item
from utils.translation_utils import t

def render_bulk_upload_form(rerun_callback=None):
    """Render the bulk upload form for multiple items"""
    st.title("Bulk Upload Items")
    
    # File uploader for multiple images
    uploaded_files = st.file_uploader(
        "Upload multiple photos",
        type=["jpg", "jpeg", "png"],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        # Create a list to store the data for each item
        items_data = []
        
        # Display the spreadsheet-like interface
        st.subheader("Enter Item Details")
        
        # Create a container for the table
        with st.container():
            # Create columns for the table headers
            col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
            
            with col1:
                st.markdown("**Photo**")
            with col2:
                st.markdown("**Item Name**")
            with col3:
                st.markdown("**USD Price**")
            with col4:
                st.markdown("**Local Price**")
            
            # Create a row for each uploaded file
            for i, uploaded_file in enumerate(uploaded_files):
                # Read the image
                image = Image.open(uploaded_file)
                
                # Resize the image for thumbnail
                image.thumbnail((100, 100))
                
                # Create columns for this row
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                
                with col1:
                    # Display the thumbnail
                    st.image(image, width=100)
                
                with col2:
                    # Item name input
                    name = st.text_input(
                        "Name",
                        key=f"name_{i}",
                        label_visibility="collapsed",
                        placeholder="Item name"
                    )
                
                with col3:
                    # USD price input
                    price_usd = st.number_input(
                        "USD",
                        key=f"usd_{i}",
                        min_value=0,
                        value=0,
                        label_visibility="collapsed"
                    )
                
                with col4:
                    # Local price input
                    price_local = st.number_input(
                        "Local",
                        key=f"local_{i}",
                        min_value=0,
                        value=0,
                        label_visibility="collapsed"
                    )
                
                # Add the data to our list
                items_data.append({
                    'image': uploaded_file,
                    'name': name,
                    'price_usd': price_usd,
                    'price_local': price_local
                })
        
        # Submit button
        if st.button("Submit All Items"):
            # Validate the data
            invalid_items = [item for item in items_data if not item['name']]
            if invalid_items:
                st.error("Please enter names for all items")
                return
            
            # Process each item
            success_count = 0
            for item in items_data:
                # Create the item data
                item_data = {
                    "name": item['name'],
                    "price_usd": int(item['price_usd']) if item['price_usd'] > 0 else None,
                    "price_local": int(item['price_local']) if item['price_local'] > 0 else None,
                    "user_id": st.session_state.user.id,
                    "sale_status": 'available',
                    "is_sold": False
                }
                
                # Add the item
                if add_item(item_data, item['image']):
                    success_count += 1
            
            # Show success message
            st.success(f"Successfully added {success_count} out of {len(items_data)} items")
            
            # Clear the cache to force reload of items
            st.cache_data.clear()
            
            # Switch to the available items view
            st.session_state.current_page = 'available'
            if rerun_callback:
                rerun_callback()
    else:
        st.info("Upload multiple photos to get started") 