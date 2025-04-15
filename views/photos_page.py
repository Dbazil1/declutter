import streamlit as st
import requests
from io import BytesIO
import zipfile
from utils.translation_utils import t
from utils.image_utils import generate_sales_photo, generate_and_store_sales_photos

def render_photos_page(items):
    st.title(t('generate_photos'))
    
    # Style selection
    style = st.radio(t('choose_photo_style'), [t('overlay'), t('extended')], horizontal=True)
    style = style.lower()
    
    # Filter for available items only
    available_items = [item for item in items if not item.get('is_sold')]
    
    if available_items:
        # Add download all button
        all_photos = []
        
        st.write(t('loading_photos'))
        
        # Create a grid layout
        cols = st.columns(3)
        for i, item in enumerate(available_items):
            if item.get('image_url'):
                with cols[i % 3]:
                    # Try to use pre-generated sales photo
                    sales_photo = None
                    if style == "overlay" and item.get('sales_overlay_url'):
                        response = requests.get(item['sales_overlay_url'])
                        if response.status_code == 200:
                            sales_photo = response.content
                    elif style == "extended" and item.get('sales_extended_url'):
                        response = requests.get(item['sales_extended_url'])
                        if response.status_code == 200:
                            sales_photo = response.content
                    
                    # Only generate if not available in storage
                    if not sales_photo:
                        sales_photo = generate_sales_photo(
                            item['image_url'],
                            item.get('price_usd'),
                            item.get('price_local'),
                            item['name'],
                            style,
                            item['id']
                        )
                        # Store the generated photo for future use
                        if sales_photo:
                            generate_and_store_sales_photos(
                                st.session_state.supabase,
                                item['id'],
                                item['image_url'],
                                item.get('price_usd'),
                                item.get('price_local'),
                                item['name']
                            )
                    
                    if sales_photo:
                        # Format price text for caption
                        if item.get('price_usd') and item.get('price_local'):
                            price_text = f"${item['price_usd']} USD / {item['price_local']} Moneda Local"
                        elif item.get('price_usd'):
                            price_text = f"${item['price_usd']} USD"
                        elif item.get('price_local'):
                            price_text = f"{item['price_local']} Moneda Local"
                        else:
                            price_text = ""
                        
                        st.image(BytesIO(sales_photo), caption=f"{item['name']} - {price_text}", width=200)
                        all_photos.append({
                            'name': item['name'],
                            'photo': sales_photo
                        })
            else:
                with cols[i % 3]:
                    st.warning(f"No image available for {item['name']}")
        
        # Add download all button if we have photos
        if all_photos:            
            # Create a ZIP file containing all photos
            zip_buffer = BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w') as zip_file:
                for photo in all_photos:
                    zip_file.writestr(
                        f"sales_photo_{photo['name'].lower().replace(' ', '_')}.jpg",
                        photo['photo']
                    )
            
            # Add download all button
            st.download_button(
                label=t('download_all'),
                data=zip_buffer.getvalue(),
                file_name="all_sales_photos.zip",
                mime="application/zip",
                key="download_all"
            )
    else:
        st.info(t('no_available_items')) 