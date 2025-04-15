import streamlit as st
from translations import translations

# Function to get translated text
def t(key, **kwargs):
    lang = st.session_state.get('language', 'en')
    text = translations[lang].get(key, key)
    return text.format(**kwargs) if kwargs else text 