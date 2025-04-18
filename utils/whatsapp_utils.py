import urllib.parse

def generate_whatsapp_message_template(item_name, item_id, price_usd=None, price_local=None, link_code=None):
    """
    Generate a bilingual template message for WhatsApp contact based on item details
    """
    # Get the item number (first 8 chars of UUID)
    item_number = item_id[:8]
    
    # Combined bilingual greeting and interest statement
    message = f"Hola/Hi! Me interesa/I'm interested in:\n"
    
    # Item details with indentation
    message += f"    {item_name} (#{item_number})\n"
    
    # Add price information if available
    if price_usd and price_local:
        message += f"    ${price_usd} USD / {price_local} moneda local\n\n"
    elif price_usd:
        message += f"    ${price_usd} USD\n\n"
    elif price_local:
        message += f"    {price_local} moneda local\n\n"
    
    # Simple closing question
    message += "Todavía está disponible? Is it available?\n\n"
    
    # Add app promotion footer with public link
    message += "Sent from Declutter\n"
    if link_code:
        message += f"https://declutter.streamlit.app?code={link_code}"
    else:
        message += "https://declutter.streamlit.app"
    
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