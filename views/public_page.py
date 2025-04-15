import streamlit as st
from services.data_service import get_public_link_by_code, load_public_items, get_user_whatsapp_info
from utils.translation_utils import t
from utils.whatsapp_utils import generate_whatsapp_message_template, create_whatsapp_link
import base64
from PIL import Image
import io

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
    
    # Get owner info including name
    owner_info = st.session_state.supabase.table('users')\
        .select('first_name')\
        .eq('id', public_link['user_id'])\
        .execute()
    
    owner_name = owner_info.data[0]['first_name'] if owner_info.data else 'User'
    
    # Get owner's WhatsApp info
    owner_whatsapp = get_user_whatsapp_info(public_link['user_id'])
    
    # Display the page title and header with owner's name
    st.title(f"{owner_name}'s " + bilingual('available_items'))
    
    if public_link.get('name'):
        st.subheader(public_link['name'])
    
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
                    st.image(item['image_url'], use_column_width=True)
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
                
                # Add WhatsApp contact button if owner has enabled it
                if (owner_whatsapp and 
                    owner_whatsapp.get('whatsapp_phone') and 
                    owner_whatsapp.get('share_whatsapp_for_items')):
                    
                    # Generate message template
                    message = generate_whatsapp_message_template(
                        item['name'],
                        item['id'],
                        item.get('price_usd'),
                        item.get('price_local')
                    )
                    
                    # Create WhatsApp link
                    whatsapp_link = create_whatsapp_link(
                        owner_whatsapp['whatsapp_phone'], 
                        message
                    )
                    
                    if whatsapp_link:
                        # Display WhatsApp button
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
                        
                        st.markdown(f'<a href="{whatsapp_link}" target="_blank" class="whatsapp-button">{bilingual("contact_via_whatsapp")}</a>', unsafe_allow_html=True) 