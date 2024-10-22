import streamlit as st

def template1_page_style():  
    #with open('/Users/maxmodlin/maxdev/Streamlit_UI_Template/templates/template1_style.css') as f:
    with open('C:\\Users\\Administrator\\theah-mvp\\templates\\template1_style.css') as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

def template2_page_style():  
    #with open('/Users/maxmodlin/maxdev/Streamlit_UI_Template/templates/template2_style.css') as f:
    with open('C:\\Users\\Administrator\\theah-mvp\\templates\\template2_style.css') as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)