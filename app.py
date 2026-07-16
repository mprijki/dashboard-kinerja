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
    .metro-card { 
        padding: 10px 5px; border-radius: 12px; color: white; margin-bottom: 10px; font-weight: bold;
        display: flex; flex-direction: column; justify-content: center; align-items: center; height: 80px;
    }
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

    def get_list_unit():
        all_units = []
        page_size = 1000
        page = 0
        while True:
            response = supabase.table("data_triwulan").select("unit_kerja").range(page * page_size, (page + 1) * page_size - 1).execute()
            if not response.data: break
            df_temp = pd.DataFrame(response.data)
            all_units.extend(df_temp['unit_kerja'].unique().tolist())
            if len(response.data) < page_size: break
            page += 1
        return sorted(list(set(all_units)))

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

    list_unit = get_list_unit()
    pilih_tempat = st.selectbox("Pilih Perangkat Daerah:", ["-- Pilih --"] + list_unit)

    if pilih_tempat != "-- Pilih --":
        df_filtered = get_data_by_filter(pilih_tempat)
        if not df_filtered.empty and 'kuadran_kinerja' in df_filtered.columns:
            df_tampil = df_filtered[['nama', 'status_penilaian']].copy()
            df_tampil.columns = ["NAMA", "STATUS PENILAIAN"]
            
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer: df_tampil.to_excel(writer, index=False)
            st.download_button("Download Excel", buffer.getvalue(), f"Data_{pilih_tempat}.xlsx", use_container_width=True)
            
            st.write("---")
            st.subheader(f"PENILAIAN TRIWULAN: {pilih_tempat}")
            
            order_kategori = ['sangat baik', 'baik', 'butuh perbaikan', 'kurang', 'sangat kurang', '0', 'tidak ada data']
            counts = df_filtered['kuadran_kinerja'].astype(str).str.lower().value_counts().reindex(order_kategori, fill_value=0).reset_index()
            counts.columns = ['Kuadran', 'Total']
            
            fig = px.bar(counts, x='Kuadran', y='Total', color='Kuadran', 
                         color_discrete_map={'sangat baik': '#399abf', 'baik': '#78c41b', 'butuh perbaikan': '#f2ed31', 
                                            'kurang': '#fac833', 'sangat kurang': '#f44336', '0': '#76328d', 'tidak ada data': '#ed462e'})
            fig.update_layout(showlegend=False, xaxis=dict(title=None, showticklabels=False), yaxis=dict(title=None), margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig, use_container_width=True)
            
            # --- LEGEND KOTAK ---
            st.markdown("""
            <div class="legend-box" style="line-height: 2;">
                <span style="color:#007bff">■</span> Sangat Baik | 
                <span style="color:#28a745">■</span> Baik | 
                <span style="color:#d4ac0d">■</span> Perbaikan<br>
                <span style="color:#fd7e14">■</span> Kurang | 
                <span style="color:#f44336">■</span> Sangat Kurang | 
                <span style="color:#566573">■</span> 0 | 
                <span style="color:#8b0000">■</span> Tidak Ada Data
            </div>
            """, unsafe_allow_html=True)
            
            df_filtered['status_clean'] = df_filtered['status_penilaian'].astype(str).str.lower().str.strip()
            s = df_filtered['status_clean'].value_counts()
            
            # --- TOMBOL KARTU ---
            c1, c2, c3 = st.columns(3)
            def toggle_filter(val): st.session_state["active_filter"] = None if st.session_state["active_filter"] == val else val
            
            if c1.button(" ", key="btn_sudah", use_container_width=True): toggle_filter("sudah")
            c1.markdown(f'<div class="metro-card" style="background:#28a745; margin-top:-65px; pointer-events:none"><span>SUDAH</span><b>{s.get("sudah", 0)}</b></div>', unsafe_allow_html=True)
            
            if c2.button(" ", key="btn_belum", use_container_width=True): toggle_filter("belum")
            c2.markdown(f'<div class="metro-card" style="background:#fd7e14; margin-top:-65px; pointer-events:none"><span>BELUM</span><b>{s.get("belum", 0)}</b></div>', unsafe_allow_html=True)
            
            if c3.button(" ", key="btn_tidak", use_container_width=True): toggle_filter("tidak ada data")
            c3.markdown(f'<div class="metro-card" style="background:#6c757d; margin-top:-65px; pointer-events:none"><span>TIDAK ADA</span><b>{s.get("tidak ada data", 0)}</b></div>', unsafe_allow_html=True)
            
            # --- LOGIKA TABEL ---
            if st.session_state["active_filter"]:
                st.write("---")
                st.subheader(f"DETAIL: {st.session_state['active_filter'].upper()}")
                df_sub = df_filtered[df_filtered['status_clean'] == st.session_state["active_filter"]][['nama', 'status_penilaian']]
                df_sub.columns = ["NAMA", "STATUS PENILAIAN"]
                
                page_size = 100
                total_data = len(df_sub)
                total_pages = (total_data // page_size) + (1 if total_data % page_size != 0 else 0)
                
                col_nav1, col_nav2 = st.columns([1, 2])
                with col_nav1:
                    page_num = st.number_input("Pilih Halaman:", min_value=1, max_value=total_pages, value=1)
                with col_nav2:
                    st.markdown(f"<br>Halaman **{page_num}** dari **{total_pages}** <br>Menampilkan data **{(page_num-1)*page_size + 1}** - **{min(page_num*page_size, total_data)}** dari **{total_data}**", unsafe_allow_html=True)
                st.markdown(df_sub.iloc[(page_num-1)*page_size : page_num*page_size].to_html(classes="custom-table", index=False), unsafe_allow_html=True)
        else: st.info("Data tidak ditemukan atau kosong.")
    else: st.info("Pilih Perangkat Daerah di atas.")
