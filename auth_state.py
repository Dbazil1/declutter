import streamlit as st

def init_auth_state():
    """Initialize authentication state variables."""
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'auth_token' not in st.session_state:
        st.session_state.auth_token = None

def set_user(user):
    """Safely set the user object in session state."""
    st.session_state.user = user

def get_user():
    """Safely get the user object from session state."""
    return st.session_state.user

def get_user_id():
    """Safely get the user ID, with validation."""
    user = get_user()
    if user and hasattr(user, 'id'):
        return user.id
    return None

def is_authenticated():
    """Check if user is authenticated with validation."""
    return get_user_id() is not None

def store_auth_token(token):
    """Store authentication token in session state."""
    st.session_state.auth_token = token

def get_auth_token():
    """Get authentication token from session state."""
    return st.session_state.auth_token if 'auth_token' in st.session_state else None

def clear_auth():
    """Clear authentication state."""
    st.session_state.user = None
    st.session_state.auth_token = None 