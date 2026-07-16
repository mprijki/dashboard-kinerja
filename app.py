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
    
    /* Tombol jadi bentuk kartu yang stabil */
    div.stButton > button {
        height: 85px !important;
        width: 100% !important;
        border-radius: 12px !important;
        font-weight: bold !important;
        border: none !important;
        transition: all 0.3s ease !important;
        color: white !important;
        display: flex !important;
        flex-direction: column !important;
        justify-content: center !important;
        align-items: center !important;
        white-space: pre-line !important;
        line-height: 1.2 !important;
    }
    div.stButton > button:hover {
        transform: scale(1.03);
        filter: brightness(1.2);
        box-shadow: 0 4px 10px rgba(0,0,0,0.3);
    }
    
    /* Warna per posisi button (pasti nempel) */
    div.stColumn:nth-of-type(1) button { background-color: #399abf !important; }
    div.stColumn:nth-of-type(2) button { background-color: #e7465d !important; }
    div.stColumn:nth-of-type(3) button { background-color: #78328b !important; }

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

    @st.cache_data(ttl=3600)
    def get_list_unit():
        response = supabase.table("data_triwulan").select("unit_kerja").execute()
        return sorted(list(set([x['unit_kerja'] for x in response.data])))

    @st.cache_data(ttl=3600)
    def get_data_by_filter(pilih_tempat):
        response = supabase.table("data_triwulan").select("*").eq("unit_kerja", pilih_tempat).execute()
        return pd.DataFrame(response.data)

    list_unit = get_list_unit()
    pilih_tempat = st.selectbox("Pilih Perangkat Daerah:", ["-- Pilih --"] + list_unit)

    if pilih_tempat != "-- Pilih --":
        df_filtered = get_data_by_filter(pilih_tempat)
        if not df_filtered.empty and 'kuadran_kinerja' in df_filtered.columns:
            
            # --- DOWNLOADER ---
            df_tampil = df_filtered[['nama', 'status_penilaian']].copy()
            df_tampil.columns = ["NAMA", "STATUS PENILAIAN"]
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer: df_tampil.to_excel(writer, index=False)
            st.download_button("Download Excel", buffer.getvalue(), f"Data_{pilih_tempat}.xlsx", use_container_width=True)
            
            st.write("---")
            st.subheader(f"PENILAIAN TRIWULAN: {pilih_tempat}")
            
            # --- CHART ---
            order_kategori = ['sangat baik', 'baik', 'butuh perbaikan', 'kurang', 'sangat kurang', '0', 'tidak ada data']
            counts = df_filtered['kuadran_kinerja'].astype(str).str.lower().value_counts().reindex(order_kategori, fill_value=0).reset_index()
            counts.columns = ['Kuadran', 'Total']
            fig = px.bar(counts, x='Kuadran', y='Total', color='Kuadran', 
                         color_discrete_map={'sangat baik': '#399abf', 'baik': '#78c41b', 'butuh perbaikan': '#f2ed31', 
                                            'kurang': '#f28530', 'sangat kurang': '#eb462e', '0': '#e7465d', 'tidak ada data': '#78328b'})
            fig.update_layout(showlegend=False, xaxis=dict(title=None, showticklabels=False), yaxis=dict(title=None), margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig, use_container_width=True)
            
            # --- LEGEND ---
            st.markdown("""
            <div class="legend-box" style="line-height: 2;">
                <span style="color:#399abf">■</span> Sangat Baik | <span style="color:#78c41b">■</span> Baik | <span style="color:#f2ed31">■</span> Perbaikan<br>
                <span style="color:#f28530">■</span> Kurang | <span style="color:#eb462e">■</span> Sangat Kurang | <span style="color:#e7465d">■</span> belum ada nilai | <span style="color:#78328b">■</span> Tidak Ada Data
            </div>
            """, unsafe_allow_html=True)
            
            # --- TOMBOL KARTU ---
            df_filtered['status_clean'] = df_filtered['status_penilaian'].astype(str).str.lower().str.strip()
            s = df_filtered['status_clean'].value_counts()
            
            c1, c2, c3 = st.columns(3)
            def toggle_filter(val): st.session_state["active_filter"] = None if st.session_state["active_filter"] == val else val
            
            if c1.button(f"SUDAH DINILAI\n{s.get('sudah', 0)}"): toggle_filter("sudah")
            if c2.button(f"BELUM DINILAI\n{s.get('belum', 0)}"): toggle_filter("belum")
            if c3.button(f"TIDAK ADA DATA\n{s.get('tidak ada data', 0)}"): toggle_filter("tidak ada data")
            
            # --- TABEL ---
            if st.session_state["active_filter"]:
                st.write("---")
                st.subheader(f"DETAIL: {st.session_state['active_filter'].upper()}")
                df_sub = df_filtered[df_filtered['status_clean'] == st.session_state["active_filter"]][['nama', 'status_penilaian']]
                df_sub.columns = ["NAMA", "STATUS PENILAIAN"]
                st.markdown(df_sub.to_html(classes="custom-table", index=False), unsafe_allow_html=True)
