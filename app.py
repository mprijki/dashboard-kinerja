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

# CSS Styling
st.markdown("""
<style>
    [data-testid="stHeader"] { display: none; }
    .block-container { padding-top: 0.5rem !important; padding-bottom: 1rem !important; }
    .stImage > img { width: 100% !important; height: auto !important; display: block !important; margin: 0 auto !important; }
    .custom-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 10px; }
    .custom-table th { background-color: #add8e6; color: black; padding: 10px; text-align: center; font-weight: 900; border: 1px solid #ddd; text-transform: uppercase !important; }
    .custom-table td { padding: 8px; text-align: center; border: 1px solid #ddd; }
    .legend-box { font-size: 12px; margin-bottom: 15px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# 2. Fungsi Auth
def verify_login(nip, password):
    response = supabase.table("users_login").select("password_hash").eq("nip", nip).execute()
    if response.data:
        stored_hash = response.data[0]["password_hash"].encode('utf-8')
        return bcrypt.checkpw(password.encode('utf-8'), stored_hash)
    return False

# 3. Session State
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "filter_status" not in st.session_state: st.session_state["filter_status"] = None

# 4. Logic Login
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
    # Header & Logout
    if os.path.exists("header.png"): st.image("header.png")
    else: st.title("LAPORAN DINAMIS KINERJA")

    if st.button("Logout", use_container_width=True):
        st.session_state["logged_in"] = False
        st.session_state["filter_status"] = None
        st.rerun()

    # Data Functions
    @st.cache_data(ttl=3600)
    def get_list_unit():
        response = supabase.table("data_triwulan").select("unit_kerja").execute()
        return sorted(list(set([x['unit_kerja'] for x in response.data])))

    @st.cache_data(ttl=3600)
    def get_data_by_filter(pilih_tempat):
        response = supabase.table("data_triwulan").select("*").eq("unit_kerja", pilih_tempat).execute()
        return pd.DataFrame(response.data)

    pilih_tempat = st.selectbox("Pilih Perangkat Daerah:", ["-- Pilih --"] + get_list_unit())

    if pilih_tempat != "-- Pilih --":
        df_filtered = get_data_by_filter(pilih_tempat)
        if not df_filtered.empty and 'kuadran_kinerja' in df_filtered.columns:
            df_tampil_raw = df_filtered[['nama', 'status_penilaian']].copy()
            df_tampil_raw.columns = ["NAMA", "STATUS PENILAIAN"]
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer: df_tampil_raw.to_excel(writer, index=False)
            st.download_button("Download Excel", buffer.getvalue(), f"Data_{pilih_tempat}.xlsx", use_container_width=True)
            
            st.write("---")
            st.subheader(f"PENILAIAN: {pilih_tempat}")
            
            # Chart
            order_k = ['sangat baik', 'baik', 'butuh perbaikan', 'kurang', 'sangat kurang', '0', 'tidak ada data']
            counts = df_filtered['kuadran_kinerja'].astype(str).str.lower().value_counts().reindex(order_k, fill_value=0).reset_index()
            fig = px.bar(counts, x='index', y='kuadran_kinerja')
            st.plotly_chart(fig, use_container_width=True)
            
            # Cards
            df_filtered['status_clean'] = df_filtered['status_penilaian'].astype(str).str.lower().str.strip()
            s = df_filtered['status_clean'].value_counts()
            c1, c2, c3 = st.columns(3)
            if c1.button(f"SUDAH\n{s.get('sudah', 0)}", use_container_width=True): st.session_state["filter_status"] = "sudah"
            if c2.button(f"BELUM\n{s.get('belum', 0)}", use_container_width=True): st.session_state["filter_status"] = "belum"
            if c3.button(f"TIDAK ADA\n{s.get('tidak ada data', 0)}", use_container_width=True): st.session_state["filter_status"] = "tidak ada data"
            
            # Tabel (Muncul pas kartu diklik)
            if st.session_state["filter_status"]:
                st.write("---")
                st.subheader(f"DETAIL: {st.session_state['filter_status'].upper()}")
                df_tabel = df_filtered[df_filtered['status_clean'] == st.session_state["filter_status"]][['nama', 'status_penilaian']]
                df_tabel.columns = ["NAMA", "STATUS PENILAIAN"]
                
                page_size = 100
                total = len(df_tabel)
                page_num = st.number_input("Halaman:", min_value=1, max_value=(total // page_size) + 1, value=1)
                st.markdown(df_tabel.iloc[(page_num-1)*page_size : page_num*page_size].to_html(classes="custom-table", index=False), unsafe_allow_html=True)
        else:
            st.info("Data kosong, Cuk.")
