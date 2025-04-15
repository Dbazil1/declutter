import streamlit as st
from utils.translation_utils import t
from components.item_components import render_item_grid, render_edit_modal, render_sold_to_view

def render_items_page(current_page, items, first_name=None):
    # Set the appropriate title and filter
    show_all = False  # Initialize show_all
    filter_status = None  # Initialize filter_status
    
    if current_page == 'all':
        st.title(t('all_items'))
        filter_status = None
        show_all = True
    elif current_page == 'available':
        st.markdown(f'<p class="greeting">{t("greeting", name=first_name)}</p>', unsafe_allow_html=True)
        st.title(t('available'))
        filter_status = None
        show_all = False
    elif current_page == 'paid_ready':
        st.title(t('paid_ready'))
        filter_status = 'paid_pending_pickup'
        show_all = False
    elif current_page == 'claimed':
        st.title(t('claimed'))
        filter_status = 'claimed_not_paid'
        show_all = False
    elif current_page == 'complete':
        st.title(t('complete'))
        filter_status = 'paid_picked_up'
        show_all = False
    elif current_page == 'sold_to':
        st.title(t('sold_to'))
        filter_status = None
        show_all = False

    # Edit Modal at the top (only shown when editing)
    render_edit_modal(rerun_callback=st.rerun)
    
    # Filter items based on status
    filtered_items = []  # Initialize filtered_items
    if show_all:
        filtered_items = items  # Show all items
    elif filter_status is None:
        if current_page == 'sold_to':
            # Pass to the specialized sold_to view renderer
            render_sold_to_view(items)
            return
        else:
            filtered_items = [item for item in items if not item.get('is_sold')]
    else:
        filtered_items = [item for item in items if item.get('sale_status') == filter_status]
    
    # Display filtered items if not in sold_to view
    if current_page != 'sold_to':
        render_item_grid(filtered_items, rerun_callback=st.rerun) 