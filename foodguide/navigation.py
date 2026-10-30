"""Preserve input drafts when Streamlit hides widgets on another workflow."""
import streamlit as st

GROUP_INPUTS = {
    'view', 'search', 'area', 'occasion', 'strict', 'open_only',
    'weight_price', 'weight_cuisine', 'weight_area', 'meal_date', 'meal_time',
}
EXPLORER_INPUTS = {
    'location_choices', 'category_choices', 'price_choices', 'occasion_choice',
    'pace_choice', 'query_choice', 'include_closed', 'max_price_choice',
}


def preserve_inputs():
    for key in list(st.session_state):
        diner_input = key.startswith('diner_') and key.endswith(('_name', '_budget', '_cuisine', '_area'))
        review_input = key.startswith(('review_author_', 'review_body_', 'review_rating_'))
        if key in GROUP_INPUTS | EXPLORER_INPUTS or diner_input or review_input:
            # Assigning an input key to itself detaches it from widget cleanup.
            # Button and file-uploader keys must never be assigned this way.
            st.session_state[key] = st.session_state[key]
