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

# CSS Styling - Pake cara paling aman
st.markdown("""
<style>
    [data-testid="stHeader"] { display: none; }
    .block-container { padding-top: 1rem !important; }
    
    /* Tombol jadi bentuk kartu dengan efek hover */
    div.stButton > button {
        height: 80px !important;
        width: 100% !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        border: none !important;
        transition: all 0.3s ease !important;
        color: white !important;
    }
    div.stButton > button:hover {
        transform: scale(1.05);
        filter: brightness(1.2);
        box-shadow: 0 4px 10px rgba(0,0,0,0.2);
    }
    
    /* Warna spesifik tiap kartu */
    button[key="btn_sudah"] { background-color: #399abf !important; }
    button[key="btn_belum"] { background-color: #e7465d !important; }
    button[key="btn_tidak"] { background-color: #78328b !important; }

    .custom-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 10px; }
    .custom-table th { background-color: #add8e6; color: black; padding: 10px; text-align: center; font-weight: 900; border: 1px solid #ddd; }
    .custom-table td { padding: 8px; text-align: center; border: 1px solid #ddd; }
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
    st.title("🔐 PERMISI DULU JANGAN ASAL NYELONONG")
    with st.form("login_form"):
        nip_input = st.text_input("NIP:")
        pass_input = st.text_input("Password:", type="password")
        if st.form_submit_button("Login"):
            if verify_login(nip_input, pass_input):
                st.session_state["logged_in"] = True
                st.rerun()
            else: st.error("NIP/PASSWORD SALAH, BANGSAT!!!")
else:
    if os.path.exists("header.png"): st.image("header.png")
    else: st.title("LAPORAN DINAMIS KINERJA")

    if st.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state["active_filter"] = None
        st.rerun()

    def get_list_unit():
        response = supabase.table("data_triwulan").select("unit_kerja").execute()
        return sorted(list(set([x['unit_kerja'] for x in response.data])))

    def get_data_by_filter(pilih_tempat):
        response = supabase.table("data_triwulan").select("*").eq("unit_kerja", pilih_tempat).execute()
        return pd.DataFrame(response.data)

    list_unit = get_list_unit()
    pilih_tempat = st.selectbox("Pilih Perangkat Daerah:", ["-- Pilih --"] + list_unit)

    if pilih_tempat != "-- Pilih --":
        df_filtered = get_data_by_filter(pilih_tempat)
        if not df_filtered.empty and 'kuadran_kinerja' in df_filtered.columns:
            
            # --- DOWNLOADER ---
            df_tampil = df_filtered[['nama', 'status_penilaian']]
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer: df_tampil.to_excel(writer, index=False)
            st.download_button("Download Excel", buffer.getvalue(), f"Data_{pilih_tempat}.xlsx", use_container_width=True)
            
            st.write("---")
            
            # --- TOMBOL KARTU ---
            df_filtered['status_clean'] = df_filtered['status_penilaian'].astype(str).str.lower().str.strip()
            s = df_filtered['status_clean'].value_counts()
            
            c1, c2, c3 = st.columns(3)
            def toggle(val): st.session_state["active_filter"] = None if st.session_state["active_filter"] == val else val
            
            if c1.button(f"SUDAH\n{s.get('sudah', 0)}", key="btn_sudah"): toggle("sudah")
            if c2.button(f"BELUM\n{s.get('belum', 0)}", key="btn_belum"): toggle("belum")
            if c3.button(f"TIDAK ADA\n{s.get('tidak ada data', 0)}", key="btn_tidak"): toggle("tidak ada data")
            
            # --- LOGIKA TABEL ---
            if st.session_state["active_filter"]:
                st.subheader(f"DETAIL: {st.session_state['active_filter'].upper()}")
                df_sub = df_filtered[df_filtered['status_clean'] == st.session_state["active_filter"]][['nama', 'status_penilaian']]
                st.markdown(df_sub.to_html(classes="custom-table", index=False), unsafe_allow_html=True)
        else: st.info("Data tidak ditemukan.")
    else: st.info("Pilih Perangkat Daerah di atas.")
