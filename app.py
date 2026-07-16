import streamlit as st
import pandas as pd
import plotly.express as px
import io
import os
import bcrypt
from supabase import create_client

# 1. Setup Koneksi
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Dashboard Kinerja", layout="centered")

# CSS Styling - RAPIH, COMPACT, & ESTETIK
st.markdown("""
<style>
    [data-testid="stHeader"] { display: none; }
    .block-container { padding-top: 0.5rem !important; padding-bottom: 1rem !important; }
    
    /* Tombol Kartu (dibuat seragam & sejajar) */
    div.stButton > button {
        height: 70px !important;
        width: 100% !important;
        border-radius: 10px !important;
        font-weight: bold !important;
        border: none !important;
        transition: all 0.3s ease !important;
        color: white !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
        line-height: 1.1 !important;
        font-size: 12px !important;
    }
    
    /* Tombol Logout Khusus (Kecil & Kontras) */
    div[data-testid="stButton"] button[kind="secondary"] {
        height: 35px !important;
        background-color: #6c757d !important;
        color: white !important;
        margin-bottom: 10px !important;
    }

    div.stButton > button:hover { transform: scale(1.03); filter: brightness(1.2); }
    
    /* Warna per posisi button */
    div.stColumn:nth-of-type(1) button { background-color: #399abf !important; }
    div.stColumn:nth-of-type(2) button { background-color: #e7465d !important; }
    div.stColumn:nth-of-type(3) button { background-color: #78328b !important; }

    .custom-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 10px; }
    .custom-table th { background-color: #add8e6; color: black; padding: 8px; text-align: center; border: 1px solid #ddd; }
    .custom-table td { padding: 6px; text-align: center; border: 1px solid #ddd; }
</style>
""", unsafe_allow_html=True)

# 2. Fungsi Auth
def verify_login(nip, password):
    response = supabase.table("users_login").select("password_hash").eq("nip", nip).execute()
    if response.data:
        stored_hash = response.data[0]["password_hash"].encode('utf-8')
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            return True
    return False

# 3. Logika Session
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "active_filter" not in st.session_state: st.session_state["active_filter"] = None

if not st.session_state["logged_in"]:
    st.title("🔐 PERMISI DULU")
    with st.form("login_form"):
        nip_input = st.text_input("NIP:")
        pass_input = st.text_input("Password:", type="password")
        if st.form_submit_button("Login"):
            if verify_login(nip_input, pass_input):
                st.session_state["logged_in"] = True
                st.rerun()
            else: st.error("NIP/PASSWORD SALAH, BANGSAT!")
else:
    if os.path.exists("header.png"): st.image("header.png")
    else: st.title("LAPORAN KINERJA")

    if st.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state["active_filter"] = None
        st.rerun()

    @st.cache_data(ttl=3600)
    def get_data_by_filter(pilih_tempat):
        response = supabase.table("data_triwulan").select("*").eq("unit_kerja", pilih_tempat).execute()
        return pd.DataFrame(response.data)

    units = sorted(list(set([x['unit_kerja'] for x in supabase.table("data_triwulan").select("unit_kerja").execute().data])))
    pilih_tempat = st.selectbox("Pilih Perangkat Daerah:", ["-- Pilih --"] + units)

    if pilih_tempat != "-- Pilih --":
        df_filtered = get_data_by_filter(pilih_tempat)
        if not df_filtered.empty:
            st.download_button("📥 Download Excel", io.BytesIO(), f"Data_{pilih_tempat}.xlsx", use_container_width=True)
            
            st.subheader(f"📊 {pilih_tempat}")
            
            # CHART COMPACT
            counts = df_filtered['kuadran_kinerja'].value_counts().reset_index()
            fig = px.bar(counts, x='kuadran_kinerja', y='count', color='kuadran_kinerja', height=250)
            fig.update_layout(showlegend=False, margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig, use_container_width=True)
            
            # TOMBOL KARTU
            s = df_filtered['status_penilaian'].astype(str).str.lower().str.strip().value_counts()
            c1, c2, c3 = st.columns(3)
            if c1.button(f"SUDAH\n{s.get('sudah', 0)}"): st.session_state["active_filter"] = "sudah"
            if c2.button(f"BELUM\n{s.get('belum', 0)}"): st.session_state["active_filter"] = "belum"
            if c3.button(f"NULL\n{s.get('tidak ada data', 0)}"): st.session_state["active_filter"] = "tidak ada data"
            
            # TABEL
            if st.session_state["active_filter"]:
                st.write("---")
                df_sub = df_filtered[df_filtered['status_penilaian'].str.lower().str.strip() == st.session_state["active_filter"]]
                st.markdown(df_sub[['nama', 'status_penilaian']].to_html(classes="custom-table", index=False), unsafe_allow_html=True)
