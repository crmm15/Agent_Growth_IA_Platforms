import streamlit as st
from pathlib import Path

def show_inicio():
    md = Path(__file__).parent.parent / 'prompts'/ 'prompt_inicial.md'
    st.title("🚀 Bienvenido a GrowthIA M&M")
    st.markdown(md.read_text())