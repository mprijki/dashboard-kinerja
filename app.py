import streamlit as st
import pandas as pd
import plotly.express as px
import io
import os
import bcrypt
from supabase import create_client

# 1. Setup
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Dashboard Kinerja", layout="centered")

# CSS
st.markdown("""
<style>
    [data-testid="stHeader"] { display: none; }
    .block-container { padding-top: 0.5rem !important; padding-bottom: 1rem !important; }
    .custom-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 10px; }
    .custom-table th { background-color: #add8e6; padding: 10px; text-align: center; border: 1px solid #ddd; text-transform: uppercase; }
    .custom-table td { padding: 8px; text-align: center; border: 1px solid #ddd; }
</style>
""", unsafe_allow_html=True)

# Auth
def verify_login(nip, password):
    response = supabase.table("users_login").select("password_hash").eq("nip", nip).execute()
    if response.data:
        stored_hash = response.data[0]["password_hash"].encode('utf-8')
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash)
    return False

# Session
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "filter_status" not in st.session_state: st.session_state["filter_status"] = None

# App Logic
if not st.session_state["logged_in"]:
    st.title("🔐 Login Dashboard")
    with st.form("login_form"):
        nip_input = st.text_input("NIP:")
        pass_input = st.text_input("Password:", type="password")
        if st.form_submit_button("Login"):
            if verify_login(nip_input, pass_input):
                st.session_state["logged_in"] = True
                st.rerun()
            else: st.error("NIP atau Password salah, Cuk!")
else:
    if os.path.exists("header.png"): st.image("header.png")
    else: st.title("LAPORAN DINAMIS KINERJA")

    if st.button("Logout", use_container_width=True):
        st.session_state["logged_in"] = False
        st.session_state["filter_status"] = None
        st.rerun()

    @st.cache_data(ttl=3600)
    def get_data(pilih_tempat):
        response = supabase.table("data_triwulan").select("*").eq("unit_kerja", pilih_tempat).execute()
        return pd.DataFrame(response.data)

    # Unit List
    units = sorted(list(set([x['unit_kerja'] for x in supabase.table("data_triwulan").select("unit_kerja").execute().data])))
    pilih_tempat = st.selectbox("Pilih Perangkat Daerah:", ["-- Pilih --"] + units)

    if pilih_tempat != "-- Pilih --":
        df = get_data(pilih_tempat)
        if not df.empty:
            # Download
            df_tampil = df[['nama', 'status_penilaian']]
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as w: df_tampil.to_excel(w, index=False)
            st.download_button("Download Excel", buffer.getvalue(), f"Data_{pilih_tempat}.xlsx", use_container_width=True)
            
            st.write("---")
            # Fixed Chart
            df['kuadran_kinerja'] = df['kuadran_kinerja'].astype(str).str.lower()
            counts = df['kuadran_kinerja'].value_counts().reset_index()
            counts.columns = ['Kuadran', 'Total']
            st.plotly_chart(px.bar(counts, x='Kuadran', y='Total'), use_container_width=True)
            
            # Cards
            df['status_clean'] = df['status_penilaian'].astype(str).str.lower().str.strip()
            s = df['status_clean'].value_counts()
            c1, c2, c3 = st.columns(3)
            if c1.button(f"SUDAH\n{s.get('sudah', 0)}", use_container_width=True): st.session_state["filter_status"] = "sudah"
            if c2.button(f"BELUM\n{s.get('belum', 0)}", use_container_width=True): st.session_state["filter_status"] = "belum"
            if c3.button(f"TIDAK ADA\n{s.get('tidak ada data', 0)}", use_container_width=True): st.session_state["filter_status"] = "tidak ada data"
            
            # Tabel Dinamis
            if st.session_state["filter_status"]:
                st.write("---")
                df_tabel = df[df['status_clean'] == st.session_state["filter_status"]][['nama', 'status_penilaian']]
                st.subheader(f"DETAIL: {st.session_state['filter_status'].upper()}")
                
                page = st.number_input("Halaman:", min_value=1, max_value=(len(df_tabel)//100)+1, value=1)
                st.markdown(df_tabel.iloc[(page-1)*100 : page*100].to_html(classes="custom-table", index=False), unsafe_allow_html=True)
