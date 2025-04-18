import urllib.parse

def generate_whatsapp_message_template(item_name, item_id, price_usd=None, price_local=None):
    """
    Generate a bilingual template message for WhatsApp contact based on item details
    """
    # Spanish message first
    message = f"¡Hola! Me interesa tu artículo: {item_name}"
    
    # Add price information if available - Spanish
    if price_usd and price_local:
        message += f" (${price_usd} USD / {price_local} moneda local)"
    elif price_usd:
        message += f" (${price_usd} USD)"
    elif price_local:
        message += f" ({price_local} moneda local)"
    
    # Add courtesy line - Spanish
    message += "\n\n¿Está disponible todavía? ¿Cuándo podría verlo?"
    
    # Add divider between languages
    message += "\n\n------------------\n\n"
    
    # English message second
    message += f"Hello! I'm interested in your item: {item_name}"
    
    # Add price information if available - English
    if price_usd and price_local:
        message += f" (${price_usd} USD / {price_local} local currency)"
    elif price_usd:
        message += f" (${price_usd} USD)"
    elif price_local:
        message += f" ({price_local} local currency)"
    
    # Add courtesy line - English
    message += "\n\nIs this item still available? When could I see it?"
    
    # Add app promotion footer
    message += "\n\n------------------"
    message += "\nEnviado por Declutter | Sent via Declutter"
    message += "\nhttps://declutter.streamlit.app"
    
    return message

def format_whatsapp_number(phone_number):
    """
    Format a phone number for WhatsApp by removing any non-digit characters
    and the leading '+' if present.
    """
    if not phone_number:
        return None
        
    # Remove any non-digit characters except the leading '+'
    cleaned = ''.join(c for c in phone_number if c.isdigit() or c == '+')
    
    # Remove the leading '+' if present (WhatsApp API doesn't use it)
    if cleaned.startswith('+'):
        cleaned = cleaned[1:]
        
    return cleaned

def create_whatsapp_link(phone_number, message):
    """
    Create a WhatsApp click-to-chat link with a pre-filled message
    
    Args:
        phone_number: Phone number in international format (with or without +)
        message: Message to pre-fill in WhatsApp
        
    Returns:
        WhatsApp web link that opens chat with pre-filled message
    """
    # Format the phone number
    formatted_phone = format_whatsapp_number(phone_number)
    
    if not formatted_phone:
        return None
        
    # URL encode the message
    encoded_message = urllib.parse.quote(message)
    
    # Create the WhatsApp link
    whatsapp_link = f"https://wa.me/{formatted_phone}?text={encoded_message}"
    
    return whatsapp_link 