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

# CSS ENGINE: Mencegah bentrok antara Login dan Dashboard
def inject_style(is_login=False):
    if is_login:
        st.markdown("""
        <style>
            [data-testid="stHeader"] { display: none; }
            /* Warna Garis & Ikon Login */
            div[data-baseweb="input"] { border-color: #d9467a !important; }
            span[data-testid="stIconMaterial"] { color: #399abf !important; }
            .stMarkdown p:has(a) { display: none !important; }
            /* Tombol Login */
            div.stButton > button { 
                background-color: #78328b !important; color: white !important; 
                border-radius: 8px !important; border: none !important; width: 100%;
            }
        </style>
        """, unsafe_allow_html=True)
    else:
        CARD_H = 55
        st.markdown(f"""
        <style>
            [data-testid="stHeader"] {{ display: none; }}
            .block-container {{ padding-top: 0.2rem !important; padding-bottom: 0.2rem !important; }}
            div[data-testid="stVerticalBlock"] {{ gap: 0.1rem !important; }}
            
            /* Warna Tombol Dashboard */
            div.stButton > button[key="Logout"] {{ background-color: #ff4b4b !important; color: white !important; }}
            div.stDownloadButton > button {{ background-color: #28a745 !important; color: white !important; }}
            
            /* Kartu Rapat */
            div.stButton > button:not([key="Logout"]) {{ 
                height: {CARD_H}px !important; background: none !important; border: none !important; 
                box-shadow: none !important; padding: 0 !important; margin: 0 !important;
            }}
            .metro-card {{ 
                padding: 5px; border-radius: 10px; color: white; font-weight: bold;
                display: flex; flex-direction: column; justify-content: center; align-items: center; 
                height: {CARD_H}px; margin-top: -{CARD_H}px; pointer-events: none;
            }}
            .custom-table {{ width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 5px; }}
            .custom-table th {{ background-color: #add8e6; color: black; padding: 5px; text-align: center; border: 1px solid #ddd; }}
            .custom-table td {{ padding: 5px; text-align: center; border: 1px solid #ddd; }}
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
    inject_style(is_login=True)
    st.title("🔐 SIGN IN")
    with st.form("login_form"):
        nip_input = st.text_input("Username:")
        pass_input = st.text_input("Password:", type="password")
        if st.form_submit_button("LOGIN"):
            if verify_login(nip_input, pass_input):
                st.session_state["logged_in"] = True
                st.rerun()
            else: st.error("NIP/PASSWORD SALAH!")
else:
    inject_style(is_login=False)
    if os.path.exists("header.png"): st.image("header.png")
    else: st.title("LAPORAN DINAMIS KINERJA")

    if st.button("Logout", key="Logout", use_container_width=True):
        st.session_state["logged_in"] = False
        st.session_state["active_filter"] = None
        st.rerun()

    # --- SISA LOGIKA APP TETAP ---
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
    st.markdown("<h5 style='text-align: center; margin-bottom: 5px;'>PENILAIAN TRIWULAN</h5>", unsafe_allow_html=True)
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
            order_kategori = ['sangat baik', 'baik', 'butuh perbaikan', 'kurang', 'sangat kurang', '0', 'tidak ada data']
            counts = df_filtered['kuadran_kinerja'].astype(str).str.lower().value_counts().reindex(order_kategori, fill_value=0).reset_index()
            counts.columns = ['Kuadran', 'Total']
            
            fig = px.bar(counts, x='Kuadran', y='Total', color='Kuadran', 
                         color_discrete_map={'sangat baik': '#399abf', 'baik': '#78c41b', 'butuh perbaikan': '#f2ed31', 
                                            'kurang': '#f28530', 'sangat kurang': '#eb462e', '0': '#e7465d', 'tidak ada data': '#78328b'})
            
            fig.update_layout(height=150, showlegend=False, xaxis=dict(title=None, showticklabels=False), yaxis=dict(title=None), margin=dict(t=5, b=5, l=5, r=5))
            st.plotly_chart(fig, use_container_width=True)

            st.markdown("""
            <div style="font-size: 11px; text-align: center; line-height: 1.5; margin-bottom: 10px;">
                <span style="color:#399abf">■</span> Sangat Baik | 
                <span style="color:#78c41b">■</span> Baik | 
                <span style="color:#f2ed31">■</span> Perbaikan<br>
                <span style="color:#f28530">■</span> Kurang | 
                <span style="color:#eb462e">■</span> Sangat Kurang | 
                <span style="color:#e7465d">■</span> Belum Ada Nilai | 
                <span style="color:#78328b">■</span> Tidak Ada Data
            </div>
            """, unsafe_allow_html=True)
            
            df_filtered['status_clean'] = df_filtered['status_penilaian'].astype(str).str.lower().str.strip()
            s = df_filtered['status_clean'].value_counts()
            
            c1, c2, c3 = st.columns(3)
            def toggle_filter(val): st.session_state["active_filter"] = None if st.session_state["active_filter"] == val else val
            
            if c1.button(" ", key="btn_sudah", on_click=toggle_filter, args=("sudah",), use_container_width=True): pass
            c1.markdown(f'<div class="metro-card" style="background:#399abf;"><span>SUDAH</span><b>{s.get("sudah", 0)}</b></div>', unsafe_allow_html=True)
            
            if c2.button(" ", key="btn_belum", on_click=toggle_filter, args=("belum",), use_container_width=True): pass
            c2.markdown(f'<div class="metro-card" style="background:#e7465d;"><span>BELUM</span><b>{s.get("belum", 0)}</b></div>', unsafe_allow_html=True)
            
            if c3.button(" ", key="btn_tidak", on_click=toggle_filter, args=("tidak ada data",), use_container_width=True): pass
            c3.markdown(f'<div class="metro-card" style="background:#78328b;"><span>TIDAK ADA</span><b>{s.get("tidak ada data", 0)}</b></div>', unsafe_allow_html=True)
            
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
