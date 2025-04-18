import streamlit as st
from services.data_service import get_public_link_by_code, load_public_items, get_user_whatsapp_info
from utils.translation_utils import t
from utils.whatsapp_utils import generate_whatsapp_message_template, create_whatsapp_link
import base64
from PIL import Image
import io
import os
from supabase import create_client

def render_public_page(link_code):
    # Custom function to display bilingual text
    def bilingual(key):
        # Temporarily save and restore the language
        current_language = st.session_state.language
        
        # Get the English version
        st.session_state.language = 'en'
        english = t(key)
        
        # Get the Spanish version
        st.session_state.language = 'es'
        spanish = t(key)
        
        # Restore original language
        st.session_state.language = current_language
        
        # Return both languages
        return f"{english} / {spanish}"
    
    # Get the public link info
    public_link = get_public_link_by_code(link_code)
    
    if not public_link:
        st.error(bilingual('invalid_link'))
        return
    
    # Load the available items for this link's owner
    items = load_public_items(public_link['user_id'])
    
    # Create a service role client for database operations
    service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
    url = os.getenv('SUPABASE_URL')
    service_client = create_client(url, service_key)
    
    # Get owner info including name
    owner_info = service_client.table('users')\
        .select('first_name, last_name')\
        .eq('id', public_link['user_id'])\
        .execute()
    
    # Get owner's first and last name
    if owner_info.data:
        owner_first_name = owner_info.data[0].get('first_name', '')
        owner_last_name = owner_info.data[0].get('last_name', '')
        owner_full_name = f"{owner_first_name} {owner_last_name}"
    else:
        owner_full_name = 'User'
    
    # Get owner's WhatsApp info
    owner_whatsapp = get_user_whatsapp_info(public_link['user_id'])
    
    # Display owner's name as main header
    st.title(owner_full_name)
    
    # Save current language
    current_language = st.session_state.language
    
    # Get translations in both languages separately for proper grammar
    st.session_state.language = 'en'
    english_title = t('available_items')
    
    st.session_state.language = 'es'
    spanish_title = t('available_items')
    
    # Restore original language
    st.session_state.language = current_language
    
    # Display bilingual subtitle
    st.header(f"{english_title} / {spanish_title}")
    
    # Display message if no items available
    if not items:
        st.info(bilingual('no_available_items_public'))
        return
    
    # Create a grid layout for items
    cols = st.columns(3)
    
    for i, item in enumerate(items):
        col = cols[i % 3]
        
        with col:
            # Create a card-like container
            with st.container():
                st.markdown("---")
                
                # Display the image
                if item.get('image_url'):
                    st.image(item['image_url'], use_container_width=True)
                else:
                    st.markdown("*No image available / Imagen no disponible*")
                
                # Display item info
                st.subheader(item['name'])
                
                # Display price information
                if item.get('price_usd') and item.get('price_local'):
                    st.write(f"{bilingual('price')}: ${item['price_usd']} USD / {item['price_local']} Local")
                elif item.get('price_usd'):
                    st.write(f"{bilingual('price')}: ${item['price_usd']} USD")
                elif item.get('price_local'):
                    st.write(f"{bilingual('price')}: {item['price_local']} Local")
                
                # Show description if available
                if item.get('description'):
                    st.markdown(f"**{bilingual('item_description')}:** {item['description']}")
                
                # Show condition if available
                if item.get('condition'):
                    st.markdown(f"**{bilingual('condition')}:** {item['condition']}")
                
                # Show category if available
                if item.get('category'):
                    st.markdown(f"**{bilingual('category')}:** {item['category']}")
                
                # Add WhatsApp CSS first (always add this CSS)
                st.markdown("""
                <style>
                .whatsapp-button {
                    background-color: #25D366;
                    color: white;
                    padding: 10px 15px;
                    border-radius: 4px;
                    text-decoration: none;
                    display: inline-block;
                    width: 100%;
                    text-align: center;
                    font-weight: bold;
                    margin-top: 10px;
                }
                </style>
                """, unsafe_allow_html=True)
                
                # Add WhatsApp contact button if owner has WhatsApp
                if owner_whatsapp and owner_whatsapp.get('whatsapp_phone'):
                    # Generate message template
                    message = generate_whatsapp_message_template(
                        item['name'],
                        item['id'],
                        item.get('price_usd'),
                        item.get('price_local'),
                        public_link['link_code']
                    )
                    
                    # Create WhatsApp link
                    whatsapp_link = create_whatsapp_link(
                        owner_whatsapp['whatsapp_phone'], 
                        message
                    )
                    
                    if whatsapp_link:
                        # Display WhatsApp button
                        st.markdown(f'<a href="{whatsapp_link}" target="_blank" class="whatsapp-button">Make me an offer via WhatsApp!</a>', unsafe_allow_html=True) 