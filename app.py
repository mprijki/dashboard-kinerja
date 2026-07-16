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

# CSS Styling - KARTU SEBAGAI TOMBOL (STABIL)
st.markdown("""
<style>
    [data-testid="stHeader"] { display: none; }
    .block-container { padding-top: 0.5rem !important; padding-bottom: 1rem !important; }
    .stImage > img { width: 100% !important; height: auto !important; display: block !important; margin: 0 auto !important; }
    
    /* Tombol transparan buat nangkep klik */
    div.stButton > button {
        background: transparent !important; border: none !important; padding: 0 !important;
        height: 80px !important; width: 100% !important; display: block !important;
    }
    
    .metro-card { 
        padding: 10px 5px; border-radius: 12px; color: white; font-weight: bold;
        display: flex; flex-direction: column; justify-content: center; align-items: center; 
        height: 80px; transition: all 0.3s ease; pointer-events: none;
    }
    .metro-card:hover { transform: scale(1.05); filter: brightness(1.2); box-shadow: 0 4px 10px rgba(0,0,0,0.3); }
    
    .custom-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 10px; }
    .custom-table th { background-color: #add8e6; color: black; padding: 10px; text-align: center; border: 1px solid #ddd; text-transform: uppercase !important; }
    .custom-table td { padding: 8px; text-align: center; border: 1px solid #ddd; }
    .legend-box { font-size: 12px; margin-bottom: 15px; text-align: center; }
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
            else: st.error("NIP/PASSWORD YANG LW MASUKIN SALAH, BANGSAT!!!")
else:
    if os.path.exists("header.png"): st.image("header.png")
    else: st.title("LAPORAN DINAMIS KINERJA")

    if st.button("Logout", use_container_width=True):
        st.session_state["logged_in"] = False
        st.session_state["active_filter"] = None
        st.rerun()

    def get_data_by_filter(pilih_tempat):
        all_data = []
        page_size = 1000
        page = 0
        while True:
            response = supabase.table("data_triwulan").select("*").eq("unit_kerja", pilih_tempat).range(page * page_size, (page + 1) * page_size - 1).execute()
            if not response.data: break
            all_data.extend(response.data)
            if len(response.data) < page_size: break
            page += 1
        return pd.DataFrame(all_data)

    list_unit = sorted(list(set([x['unit_kerja'] for x in supabase.table("data_triwulan").select("unit_kerja").execute().data])))
    pilih_tempat = st.selectbox("Pilih Perangkat Daerah:", ["-- Pilih --"] + list_unit)

    if pilih_tempat != "-- Pilih --":
        df_filtered = get_data_by_filter(pilih_tempat)
        if not df_filtered.empty and 'kuadran_kinerja' in df_filtered.columns:
            
            # --- DOWNLOAD & CHART ---
            df_tampil = df_filtered[['nama', 'status_penilaian']].copy()
            df_tampil.columns = ["NAMA", "STATUS PENILAIAN"]
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer: df_tampil.to_excel(writer, index=False)
            st.download_button("Download Excel", buffer.getvalue(), f"Data_{pilih_tempat}.xlsx", use_container_width=True)
            
            st.write("---")
            st.subheader(f"PENILAIAN TRIWULAN: {pilih_tempat}")
            
            counts = df_filtered['kuadran_kinerja'].astype(str).str.lower().value_counts().reset_index()
            counts.columns = ['Kuadran', 'Total']
            fig = px.bar(counts, x='Kuadran', y='Total', color='Kuadran')
            fig.update_layout(showlegend=False, xaxis=dict(title=None, showticklabels=False), yaxis=dict(title=None, showticklabels=False), margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig, use_container_width=True)
            
            # --- TOMBOL KARTU ---
            df_filtered['status_clean'] = df_filtered['status_penilaian'].astype(str).str.lower().str.strip()
            s = df_filtered['status_clean'].value_counts()
            
            c1, c2, c3 = st.columns(3)
            def btn_card(col, label, val, color, key):
                if col.button(" ", key=f"btn_{key}"): st.session_state["active_filter"] = key
                col.markdown(f'<div class="metro-card" style="background:{color}; margin-top:-95px;"><span>{label}</span><b>{val}</b></div>', unsafe_allow_html=True)
            
            btn_card(c1, "SUDAH DINILAI", s.get("sudah", 0), "#399abf", "sudah")
            btn_card(c2, "BELUM DINILAI", s.get("belum", 0), "#e7465d", "belum")
            btn_card(c3, "TIDAK ADA DATA", s.get("tidak ada data", 0), "#78328b", "tidak ada data")
            
            # --- TABEL ---
            if st.session_state["active_filter"]:
                st.write("---")
                st.subheader(f"DETAIL: {st.session_state['active_filter'].upper()}")
                df_sub = df_filtered[df_filtered['status_clean'] == st.session_state["active_filter"]][['nama', 'status_penilaian']]
                df_sub.columns = ["NAMA", "STATUS PENILAIAN"]
                st.markdown(df_sub.to_html(classes="custom-table", index=False), unsafe_allow_html=True)
