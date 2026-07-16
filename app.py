import streamlit as st
import pandas as pd
import plotly.express as px
import io
import os
import bcrypt
from supabase import create_client

# Setup Koneksi
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Dashboard Kinerja", layout="centered")

# CSS RAPI: Tombol dan Kartu jadi SATU objek (Container)
st.markdown("""
<style>
    [data-testid="stHeader"] { display: none; }
    
    /* Container pembungkus tombol agar responsif */
    .metro-wrapper {
        position: relative;
        width: 100%;
        height: 80px;
        margin-bottom: 10px;
        cursor: pointer;
        transition: all 0.2s ease;
    }
    
    /* Tombol jadi overlay transparan penuh di atas */
    div.stButton > button {
        position: absolute !important;
        width: 100% !important;
        height: 100% !important;
        background: transparent !important;
        border: none !important;
        z-index: 10 !important;
    }

    /* Visual Kartu - Sekarang jadi child dari wrapper */
    .metro-card { 
        width: 100%; height: 100%;
        padding: 10px 5px; border-radius: 12px; color: white; font-weight: bold;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        transition: all 0.2s ease;
        z-index: 1 !important;
    }

    /* Efek hover nempel di wrapper */
    .metro-wrapper:hover .metro-card {
        transform: scale(1.03);
        filter: brightness(1.2);
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    
    .custom-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 10px; }
    .custom-table th { background-color: #add8e6; color: black; padding: 10px; text-align: center; font-weight: 900; border: 1px solid #ddd; }
    .custom-table td { padding: 8px; text-align: center; border: 1px solid #ddd; }
</style>
""", unsafe_allow_html=True)

# (Fungsi Auth dan Session State tetep sama)
# ... [Biarkan fungsi verify_login & setup session di sini] ...

# LOGIKA UTAMA RAPI
if st.session_state.get("logged_in"):
    # ... [Ambil data & hitung 's'] ...
    
    c1, c2, c3 = st.columns(3)
    def toggle_filter(val): st.session_state["active_filter"] = None if st.session_state["active_filter"] == val else val

    # Bikin fungsi biar kodingan gak ngulang-ngulang (DRY - Don't Repeat Yourself)
    def display_metro_card(col, label, color, val, key):
        with col:
            # Tombol sebagai pemicu logika
            if st.button(" ", key=key, use_container_width=True):
                toggle_filter(val)
            # Kartu sebagai visual data
            st.markdown(f'''
                <div class="metro-wrapper">
                    <div class="metro-card" style="background:{color};">
                        <span>{label}</span><b>{s.get(val, 0)}</b>
                    </div>
                </div>
            ''', unsafe_allow_html=True)

    display_metro_card(c1, "SUDAH DINILAI", "#399abf", "sudah", "btn1")
    display_metro_card(c2, "BELUM DINILAI", "#e7465d", "belum", "btn2")
    display_metro_card(c3, "TIDAK ADA DATA", "#78328b", "tidak ada data", "btn3")

    # ... [Lanjut logika display detail] ...
