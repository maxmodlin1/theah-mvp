import streamlit as st
import os

def template1_page_style():  
    script_dir = os.path.dirname(__file__)
    css_path = os.path.join(script_dir, '../templates/template1_style.css')
    with open(css_path) as f:
        css = f.read()
        st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)

def template2_page_style():  
    script_dir = os.path.dirname(__file__)
    css_path = os.path.join(script_dir, '../templates/template2_style.css')
    with open(css_path) as f:
        css = f.read()
    st.markdown(f'<style>{css}</style>', unsafe_allow_html=True)