import requests
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
import streamlit as st
import uuid
import time

# Function to generate sales photos
def generate_sales_photo(image_url, price_usd, price_local, item_name, style="overlay", item_id=None):
    try:
        # Check cache first if item_id is provided
        if item_id:
            cached_photo = get_cached_sales_photo(item_id, style)
            if cached_photo:
                return cached_photo

        # Download the image
        response = requests.get(image_url)
        if response.status_code != 200:
            return None
            
        # Open the image and convert to RGB if needed
        img = Image.open(BytesIO(response.content))
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize large images to max 1920x1080 while maintaining aspect ratio
        max_width = 1920
        max_height = 1080
        if img.width > max_width or img.height > max_height:
            ratio = min(max_width/img.width, max_height/img.height)
            new_size = (int(img.width * ratio), int(img.height * ratio))
            img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        # Create a drawing context
        draw = ImageDraw.Draw(img)
        
        # Calculate font sizes with minimum sizes
        title_size_percent = 0.06   # Increased from 0.045 to 0.06 (6% of image width)
        price_size_percent = 0.075  # Increased from 0.06 to 0.075 (7.5% of image width)
        min_title_size = 36        # Increased from 24 to 36
        min_price_size = 42        # Increased from 32 to 42
        
        title_font_size = max(int(img.width * title_size_percent), min_title_size)
        price_font_size = max(int(img.width * price_size_percent), min_price_size)
        
        # Try to load a font
        try:
            # Try different font paths
            font_paths = [
                "/System/Library/Fonts/Arial.ttf",  # macOS
                "/usr/share/fonts/truetype/arial.ttf",  # Linux
                "C:\\Windows\\Fonts\\arial.ttf"  # Windows
            ]
            title_font = None
            price_font = None
            
            for path in font_paths:
                try:
                    title_font = ImageFont.truetype(path, title_font_size)
                    price_font = ImageFont.truetype(path, price_font_size)
                    break
                except:
                    continue
            
            if not title_font or not price_font:
                raise Exception("No suitable font found")
                
        except:
            # Use default font if no system font is available
            title_font = ImageFont.load_default()
            price_font = ImageFont.load_default()
        
        # Format price text
        if price_usd and price_local:
            price_text = f"${price_usd} USD / {price_local} Moneda Local"
        elif price_usd:
            price_text = f"${price_usd} USD"
        elif price_local:
            price_text = f"{price_local} Moneda Local"
        else:
            price_text = ""  # No prices available
        
        if style == "extended":
            # Create a new image with extra space at the bottom
            extension_height = int(img.height * 0.25)  # 25% of original height
            new_img = Image.new('RGB', (img.width, img.height + extension_height), (255, 255, 255))
            new_img.paste(img, (0, 0))
            
            # Create a new drawing context for the extended image
            draw = ImageDraw.Draw(new_img)
            
            # Calculate text dimensions
            title_bbox = draw.textbbox((0, 0), item_name, font=title_font)
            price_bbox = draw.textbbox((0, 0), price_text, font=price_font)
            
            # Center the text in the extended space
            title_x = (img.width - (title_bbox[2] - title_bbox[0])) // 2
            price_x = (img.width - (price_bbox[2] - price_bbox[0])) // 2
            
            # Position text in the extended space with better spacing
            title_y = img.height + (extension_height * 0.25)  # 25% into the extension
            price_y = img.height + (extension_height * 0.65)  # 65% into the extension
            
            # Add the text
            draw.text((title_x, title_y), item_name, fill=(0, 0, 0), font=title_font)
            draw.text((price_x, price_y), price_text, fill=(0, 0, 0), font=price_font)
            
            # Use the new image
            img = new_img
            
        else:  # overlay style
            # Calculate text dimensions
            title_bbox = draw.textbbox((0, 0), item_name, font=title_font)
            price_bbox = draw.textbbox((0, 0), price_text, font=price_font)
            
            # Calculate positions (bottom center with padding)
            title_x = (img.width - (title_bbox[2] - title_bbox[0])) // 2
            price_x = (img.width - (price_bbox[2] - price_bbox[0])) // 2
            
            # Position text with padding from bottom
            title_y = int(img.height * 0.82) - (title_bbox[3] - title_bbox[1])  # Moved up from 0.85
            price_y = int(img.height * 0.92) - (price_bbox[3] - price_bbox[1])  # Moved up from 0.95
            
            # Add semi-transparent background for text with better contrast
            background_height = int(img.height * 0.3)  # Increased from 0.25 to 0.3 (30% of image height)
            background = Image.new('RGBA', (img.width, background_height), (0, 0, 0, 200))  # Increased opacity from 180 to 200
            img.paste(background, (0, img.height - background_height), background)
            
            # Create a new drawing context after pasting the background
            draw = ImageDraw.Draw(img)
            
            # Add text shadow for better readability
            shadow_offset = 3  # Increased from 2 to 3
            draw.text((title_x + shadow_offset, title_y + shadow_offset), item_name, fill=(0, 0, 0, 160), font=title_font)  # Increased shadow opacity
            draw.text((price_x + shadow_offset, price_y + shadow_offset), price_text, fill=(0, 0, 0, 160), font=price_font)  # Increased shadow opacity
            
            # Add the main text
            draw.text((title_x, title_y), item_name, fill=(255, 255, 255), font=title_font)
            draw.text((price_x, price_y), price_text, fill=(255, 255, 255), font=price_font)
        
        # Save with slightly reduced quality for better performance
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='JPEG', quality=85)
        img_byte_arr = img_byte_arr.getvalue()
        
        # Cache the result if item_id is provided
        if item_id:
            cache_sales_photo(item_id, img_byte_arr, style)
        
        return img_byte_arr
    except Exception as e:
        st.error(f"Error generating sales photo: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        return None

# Cache generated sales photos in session state
def get_cached_sales_photo(item_id, style="overlay"):
    cache_key = f"sales_photo_{item_id}_{style}"
    return st.session_state.get(cache_key)

def cache_sales_photo(item_id, photo_bytes, style="overlay"):
    cache_key = f"sales_photo_{item_id}_{style}"
    st.session_state[cache_key] = photo_bytes

# Function to generate and store sales photos
def generate_and_store_sales_photos(supabase, item_id, image_url, price_usd, price_local, item_name):
    try:
        # Generate both styles of sales photos
        overlay_photo = generate_sales_photo(image_url, price_usd, price_local, item_name, "overlay", item_id)
        extended_photo = generate_sales_photo(image_url, price_usd, price_local, item_name, "extended", item_id)
        
        if overlay_photo and extended_photo:
            # Generate unique filenames with timestamp to prevent caching
            timestamp = int(time.time())
            overlay_filename = f"{item_id}/sales_overlay_{timestamp}.jpg"
            extended_filename = f"{item_id}/sales_extended_{timestamp}.jpg"
            
            # Upload overlay version
            supabase.storage\
                .from_('item-images')\
                .upload(overlay_filename, overlay_photo, {
                    'content-type': 'image/jpeg',
                    'cache-control': 'no-cache'
                })
            
            # Upload extended version
            supabase.storage\
                .from_('item-images')\
                .upload(extended_filename, extended_photo, {
                    'content-type': 'image/jpeg',
                    'cache-control': 'no-cache'
                })
            
            # Get public URLs
            overlay_url = supabase.storage\
                .from_('item-images')\
                .get_public_url(overlay_filename)
            
            extended_url = supabase.storage\
                .from_('item-images')\
                .get_public_url(extended_filename)
            
            # Update the item_images table with the new URLs
            supabase.table('item_images')\
                .update({
                    'sales_image_overlay_url': overlay_url,
                    'sales_image_extended_url': extended_url
                })\
                .eq('item_id', item_id)\
                .execute()
            
            # Clear all caches
            st.cache_data.clear()
            
            return True
    except Exception as e:
        st.error(f"Error generating sales photos: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
    return False 