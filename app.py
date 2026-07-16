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

# --- CSS ENGINE (Login & Dashboard Terpisah) ---
def inject_css(is_login=False):
    if is_login:
        st.markdown("""
        <style>
            [data-testid="stHeader"] { display: none; }
            .block-container { max-width: 400px !important; padding-top: 5rem !important; }
            /* Garis bawah pink */
            div[data-baseweb="input"] { 
                background: transparent !important; border: none !important; 
                border-bottom: 2px solid #d9467a !important; border-radius: 0 !important; 
            }
            /* Ikon Biru */
            span[data-testid="stIconMaterial"] { color: #399abf !important; }
            /* Hapus Label & Register */
            label { display: none !important; }
            .stMarkdown p:has(a) { display: none !important; }
            /* Tombol Login Ungu */
            div.stButton > button { 
                background-color: #78328b !important; color: white !important; 
                border: none !important; border-radius: 5px !important; width: 100%;
                font-weight: bold; padding: 10px !important;
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
            
            div.stButton > button[key="Logout"] {{ background-color: #ff4b4b !important; color: white !important; }}
            div.stDownloadButton > button {{ background-color: #28a745 !important; color: white !important; }}
            
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
        if bcrypt.checkpw(password.encode('utf-8'), stored_hash): return True
    return False

# 3. Logika Session
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "active_filter" not in st.session_state: st.session_state["active_filter"] = None

# 4. Router Halaman
if not st.session_state["logged_in"]:
    inject_css(is_login=True)
    st.markdown("<h2 style='text-align: center;'>SIGN IN</h2>", unsafe_allow_html=True)
    nip_input = st.text_input("Username", placeholder="Username")
    pass_input = st.text_input("Password", type="password", placeholder="Password")
    if st.button("LOGIN"):
        if verify_login(nip_input, pass_input):
            st.session_state["logged_in"] = True
            st.rerun()
        else: st.error("NIP/PASSWORD SALAH!")
else:
    inject_css(is_login=False)
    if os.path.exists("header.png"): st.image("header.png")
    else: st.title("LAPORAN DINAMIS KINERJA")

    if st.button("Logout", key="Logout", use_container_width=True):
        st.session_state["logged_in"] = False
        st.session_state["active_filter"] = None
        st.rerun()

    # --- LOGIKA DATA (Cached) ---
    @st.cache_data(ttl=3600)
    def get_list_unit():
        response = supabase.table("data_triwulan").select("unit_kerja").execute()
        return sorted(list(set(pd.DataFrame(response.data)['unit_kerja'])))

    @st.cache_data(ttl=3600)
    def get_data_by_filter(pilih_tempat):
        response = supabase.table("data_triwulan").select("*").eq("unit_kerja", pilih_tempat).execute()
        return pd.DataFrame(response.data)

    pilih_tempat = st.selectbox("Pilih Perangkat Daerah:", ["-- Pilih --"] + get_list_unit())

    if pilih_tempat != "-- Pilih --":
        df_filtered = get_data_by_filter(pilih_tempat)
        if not df_filtered.empty:
            df_tampil = df_filtered[['nama', 'status_penilaian']]
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer: df_tampil.to_excel(writer, index=False)
            st.download_button("Download Excel", buffer.getvalue(), f"Data_{pilih_tempat}.xlsx", use_container_width=True)
            
            st.write("---")
            counts = df_filtered['kuadran_kinerja'].value_counts().reset_index()
            fig = px.bar(counts, x='kuadran_kinerja', y='count', color='kuadran_kinerja')
            fig.update_layout(height=150, showlegend=False, margin=dict(t=5, b=5, l=5, r=5))
            st.plotly_chart(fig, use_container_width=True)
            
            st.markdown("""
            <div style="font-size: 11px; text-align: center; line-height: 1.5; margin-bottom: 10px;">
                <span style="color:#399abf">■</span> Sangat Baik | <span style="color:#78c41b">■</span> Baik | <span style="color:#f2ed31">■</span> Perbaikan<br>
                <span style="color:#f28530">■</span> Kurang | <span style="color:#eb462e">■</span> Sangat Kurang | <span style="color:#e7465d">■</span> Belum Ada Nilai | <span style="color:#78328b">■</span> Tidak Ada Data
            </div>
            """, unsafe_allow_html=True)
