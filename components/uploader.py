# components/uploader.py

import streamlit as st


def file_uploader_component():
    uploaded_file = st.sidebar.file_uploader("Upload your `.twbx` file", type=["twbx"])
    return uploaded_file
