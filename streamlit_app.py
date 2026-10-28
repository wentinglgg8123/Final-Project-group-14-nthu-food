"""Streamlit Cloud entry point. Run: streamlit run streamlit_app.py."""
from pathlib import Path

import streamlit as st

st.set_page_config(page_title='清食指南｜清大餐廳選擇器', page_icon='🍚', layout='wide')
st.markdown('''<style>
.block-container {padding: 0.5rem 0.5rem 0; max-width: 1500px;}
</style>''', unsafe_allow_html=True)

site = Path(__file__).resolve().parent / 'streamlit_assets' / 'site.html'
if not site.is_file():
    st.error('缺少網站建置檔。請在本機執行 npm ci 與 npm run build，再將 streamlit_assets/site.html 推送到 GitHub。')
    st.stop()

# All recommendation logic runs in the bundled browser app, with no API secrets.
st.iframe(site, height='content', alt='清食指南餐廳選擇器')
