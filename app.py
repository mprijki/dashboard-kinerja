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

# --- FUNGSI AUTH ---
def verify_login(nip, password):
    response = supabase.table("users_login").select("password_hash").eq("nip", nip).execute()
    if response.data:
        stored_hash = response.data[0]["password_hash"].encode('utf-8')
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash):
            return True
    return False

# --- CSS STYLING ---
st.markdown("""
<style>
    [data-testid="stHeader"] { display: none; }
    .block-container { padding-top: 0.5rem !important; padding-bottom: 1rem !important; }
    .metro-card { padding: 10px 5px; border-radius: 12px; color: white; margin-bottom: 10px; font-weight: bold; display: flex; flex-direction: column; justify-content: center; align-items: center; height: 80px; }
    .custom-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 10px; }
    .custom-table th { background-color: #add8e6; color: black; padding: 10px; text-align: center; font-weight: 900; border: 1px solid #ddd; }
    .custom-table td { padding: 8px; text-align: center; border: 1px solid #ddd; }
</style>
""", unsafe_allow_html=True)

# --- LOGIKA LOGIN ---
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    st.title("🔐 Login Dashboard")
    nip_input = st.text_input("NIP:")
    pass_input = st.text_input("Password:", type="password")
    if st.button("Login"):
        if verify_login(nip_input, pass_input):
            st.session_state["logged_in"] = True
            st.rerun()
        else:
            st.error("NIP atau Password salah, Cuk!")
else:
    # --- DASHBOARD KINERJA (MASUK KE SINI) ---
    if st.sidebar.button("Logout"):
        st.session_state["logged_in"] = False
        st.rerun()

    # Fungsi Data
    @st.cache_data(ttl=3600)
    def get_list_unit():
        # ... (fungsi list unit lu) ...
        response = supabase.table("data_triwulan").select("unit_kerja").execute()
        return sorted(list(set([x['unit_kerja'] for x in response.data])))

    @st.cache_data(ttl=3600)
    def get_data_by_filter(pilih_tempat):
        # ... (fungsi get data lu) ...
        response = supabase.table("data_triwulan").select("*").eq("unit_kerja", pilih_tempat).execute()
        return pd.DataFrame(response.data)

    # UI Dashboard
    if os.path.exists("header.png"): st.image("header.png")
    else: st.title("LAPORAN DINAMIS KINERJA")

    list_unit = get_list_unit()
    pilih_tempat = st.selectbox("Pilih Perangkat Daerah:", ["-- Pilih --"] + list_unit)

    if pilih_tempat != "-- Pilih --":
        df_filtered = get_data_by_filter(pilih_tempat)
        if not df_filtered.empty:
            # ... (Lanjutin kode chart, tabel, dll di sini) ...
            st.write("Data berhasil dimuat!")
