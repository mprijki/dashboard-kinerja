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

# CSS Styling - Tombol jadi Kartu Data
st.markdown("""
<style>
    [data-testid="stHeader"] { display: none; }
    .block-container { padding-top: 0.5rem !important; }
    
    /* Styling Tombol biar jadi Kartu */
    div[data-testid="stVerticalBlock"] div[data-testid="stButton"] button {
        width: 100% !important;
        height: 85px !important;
        border-radius: 12px !important;
        border: none !important;
        transition: all 0.2s ease !important;
        padding: 0 !important;
        color: white !important;
    }
    div[data-testid="stVerticalBlock"] div[data-testid="stButton"] button:hover {
        transform: scale(1.03) !important;
        box-shadow: 0 6px 15px rgba(0,0,0,0.3) !important;
    }
    
    .custom-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 10px; }
    .custom-table th { background-color: #add8e6; color: black; padding: 10px; text-align: center; font-weight: 900; border: 1px solid #ddd; text-transform: uppercase !important; }
    .custom-table td { padding: 8px; text-align: center; border: 1px solid #ddd; }
    .legend-box { font-size: 12px; margin-bottom: 15px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# Fungsi Auth
def verify_login(nip, password):
    response = supabase.table("users_login").select("password_hash").eq("nip", nip).execute()
    if response.data:
        stored_hash = response.data[0]["password_hash"].encode('utf-8')
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash): return True
    return False

# Fungsi buat nampilin Tombol Kartu
def display_metro_card(col, label, color, val, key, data_s, toggle_func):
    with col:
        st.markdown(f"""<style>button[key="{key}"] {{ background-color: {color} !important; }}</style>""", unsafe_allow_html=True)
        label_html = f"""<div style="text-align:center; line-height:1.2;">
            <div style="font-size:11px;">{label}</div>
            <div style="font-size:20px; font-weight:900;">{data_s.get(val, 0)}</div>
        </div>"""
        if st.button(label_html, key=key, use_container_width=True):
            toggle_func(val)

# Session State
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

    if st.button("Logout", use_container_width=True):
        st.session_state["logged_in"] = False
        st.session_state["active_filter"] = None
        st.rerun()

    @st.cache_data(ttl=3600)
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

    @st.cache_data(ttl=3600)
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
                                            'kurang': '#f28530', 'sangat kurang': '#eb462e', '0': '#e7465d', 'tidak ada data': '#78328b'})
            fig.update_layout(showlegend=False, xaxis=dict(title=None, showticklabels=False), yaxis=dict(title=None), margin=dict(t=10, b=10, l=10, r=10))
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("""
            <div class="legend-box" style="line-height: 2;">
                <span style="color:#399abf">■</span> Sangat Baik | <span style="color:#78c41b">■</span> Baik | <span style="color:#f2ed31">■</span> Perbaikan<br>
                <span style="color:#f28530">■</span> Kurang | <span style="color:#eb462e">■</span> Sangat Kurang | <span style="color:#e7465d">■</span> belum ada nilai | <span style="color:#78328b">■</span> Tidak Ada Data
            </div>
            """, unsafe_allow_html=True)
            
            df_filtered['status_clean'] = df_filtered['status_penilaian'].astype(str).str.lower().str.strip()
            s = df_filtered['status_clean'].value_counts()
            
            c1, c2, c3 = st.columns(3)
            def toggle_filter(val): st.session_state["active_filter"] = None if st.session_state["active_filter"] == val else val
            
            display_metro_card(c1, "SUDAH DINILAI", "#399abf", "sudah", "btn1", s, toggle_filter)
            display_metro_card(c2, "BELUM DINILAI", "#e7465d", "belum", "btn2", s, toggle_filter)
            display_metro_card(c3, "TIDAK ADA DATA", "#78328b", "tidak ada data", "btn3", s, toggle_filter)
            
            if st.session_state["active_filter"]:
                st.write("---")
                st.subheader(f"DETAIL: {st.session_state['active_filter'].upper()}")
                df_sub = df_filtered[df_filtered['status_clean'] == st.session_state["active_filter"]][['nama', 'status_penilaian']]
                df_sub.columns = ["NAMA", "STATUS PENILAIAN"]
                
                page_size = 100
                total_data = len(df_sub)
                total_pages = max(1, (total_data // page_size) + (1 if total_data % page_size != 0 else 0))
                
                col_nav1, col_nav2 = st.columns([1, 2])
                with col_nav1:
                    page_num = st.number_input("Pilih Halaman:", min_value=1, max_value=total_pages, value=1)
                with col_nav2:
                    st.markdown(f"<br>Halaman **{page_num}** dari **{total_pages}** <br>Menampilkan data **{(page_num-1)*page_size + 1}** - **{min(page_num*page_size, total_data)}** dari **{total_data}**", unsafe_allow_html=True)
                st.markdown(df_sub.iloc[(page_num-1)*page_size : page_num*page_size].to_html(classes="custom-table", index=False), unsafe_allow_html=True)
        else: st.info("Data tidak ditemukan atau kosong.")
    else: st.info("Pilih Perangkat Daerah di atas.")
