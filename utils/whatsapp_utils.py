import urllib.parse

def generate_whatsapp_message_template(item_name, item_id, price_usd=None, price_local=None, link_code=None, offer_amount=None):
    """
    Generate a bilingual template message for WhatsApp contact based on item details
    """
    # Get the item number (first 8 chars of UUID)
    item_number = item_id[:8]
    
    # Start with the interest statement
    message = "I'm interested in / Me interesa:\n\n"
    
    # Item details
    message += f"{item_name} (#{item_number})\n\n"
    
    # Add original price information if available
    if price_usd and price_local:
        message += f"Original Price / Precio Original: ${price_usd} USD / {price_local} moneda local\n\n"
    elif price_usd:
        message += f"Original Price / Precio Original: ${price_usd} USD\n\n"
    elif price_local:
        message += f"Original Price / Precio Original: {price_local} moneda local\n\n"
    
    # Add offer section
    message += "My Offer / Mi Oferta: \n\n"
    
    # Add separator and footer
    message += "___\n"
    message += "sent from declutter.streamlit.app"
    if link_code:
        message += f"/?code={link_code}"
    
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