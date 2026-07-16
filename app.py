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

# CSS Styling - RAPIH & GAK NGERUSAK LAYOUT
st.markdown("""
<style>
    [data-testid="stHeader"] { display: none; }
    .block-container { padding-top: 1rem !important; }
    
    /* Tombol jadi bentuk kartu yang stabil */
    div.stButton > button {
        height: 100px !important;
        width: 100% !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        border: none !important;
        transition: 0.3s !important;
        color: white !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
    }
    div.stButton > button:hover {
        transform: scale(1.02);
        filter: brightness(1.1);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
    .custom-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 10px; }
    .custom-table th { background-color: #add8e6; color: black; padding: 10px; text-align: center; border: 1px solid #ddd; }
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
    st.title("🔐 PERMISI DULU")
    with st.form("login_form"):
        nip_input = st.text_input("NIP:")
        pass_input = st.text_input("Password:", type="password")
        if st.form_submit_button("Login"):
            if verify_login(nip_input, pass_input):
                st.session_state["logged_in"] = True
                st.rerun()
            else: st.error("SALAH, BANGSAT!")
else:
    if st.button("Logout"):
        st.session_state["logged_in"] = False
        st.rerun()

    def get_data(pilih_tempat):
        response = supabase.table("data_triwulan").select("*").eq("unit_kerja", pilih_tempat).execute()
        return pd.DataFrame(response.data)

    list_unit = sorted(list(set([x['unit_kerja'] for x in supabase.table("data_triwulan").select("unit_kerja").execute().data])))
    pilih_tempat = st.selectbox("Pilih Perangkat Daerah:", ["-- Pilih --"] + list_unit)

    if pilih_tempat != "-- Pilih --":
        df = get_data(pilih_tempat)
        
        # --- CHART ---
        order = ['sangat baik', 'baik', 'butuh perbaikan', 'kurang', 'sangat kurang', '0', 'tidak ada data']
        counts = df['kuadran_kinerja'].astype(str).str.lower().value_counts().reindex(order, fill_value=0).reset_index()
        fig = px.bar(counts, x='kuadran_kinerja', y='count', color='kuadran_kinerja')
        fig.update_layout(showlegend=False, margin=dict(t=20, b=20, l=20, r=20))
        st.plotly_chart(fig, use_container_width=True)
        
        # --- TOMBOL KARTU (WARNA DITENTUKAN VIA CSS INJECTION) ---
        s = df['status_penilaian'].astype(str).str.lower().str.strip().value_counts()
        
        st.markdown(f"""<style>
            button[key="b1"] {{ background-color: #399abf !important; }}
            button[key="b2"] {{ background-color: #e7465d !important; }}
            button[key="b3"] {{ background-color: #78328b !important; }}
        </style>""", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        if c1.button(f"SUDAH\n{s.get('sudah', 0)}", key="b1"): st.session_state["active_filter"] = "sudah"
        if c2.button(f"BELUM\n{s.get('belum', 0)}", key="b2"): st.session_state["active_filter"] = "belum"
        if c3.button(f"TIDAK ADA\n{s.get('tidak ada data', 0)}", key="b3"): st.session_state["active_filter"] = "tidak ada data"
        
        if st.session_state["active_filter"]:
            st.write("---")
            st.subheader(f"DETAIL: {st.session_state['active_filter'].upper()}")
            df_sub = df[df['status_penilaian'].astype(str).str.lower().str.strip() == st.session_state["active_filter"]][['nama', 'status_penilaian']]
            st.markdown(df_sub.to_html(classes="custom-table", index=False), unsafe_allow_html=True)
