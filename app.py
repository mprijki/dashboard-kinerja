import streamlit as st
import pandas as pd
import plotly.express as px
import io
from supabase import create_client

# Setup Koneksi
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

# Pake centered biar gak meluber di monitor lebar, tapi rapi di HP
st.set_page_config(page_title="Dashboard Kinerja", layout="centered")

# CSS Styling Total - Pake max-width biar gak ambyar
st.markdown("""
<style>
    .main { max-width: 800px; margin: 0 auto; }
    .header-img { width: 100%; max-width: 400px; display: block; margin: 0 auto 20px auto; }
    .metro-card { padding: 15px; border-radius: 12px; color: white; text-align: center; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
    
    /* Tabel Cantik & Rapi */
    .custom-table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 14px; }
    .custom-table th { background-color: #add8e6; color: black; padding: 12px; text-align: center; font-weight: 800; border: 1px solid #ddd; }
    .custom-table td { padding: 10px; text-align: center; border: 1px solid #ddd; }
</style>
""", unsafe_allow_html=True)

# 1. Header Gambar (Gede & Center)
try:
    st.markdown('<img src="header.png" class="header-img">', unsafe_allow_html=True)
except:
    st.title("📊 Dashboard Kinerja")

# Fungsi Data (Paginasi)
@st.cache_data(ttl=3600)
def get_list_unit():
    # ... fungsi list_unit lu ...
    return sorted(list(set(["Unit A", "Unit B"])))

@st.cache_data(ttl=3600)
def get_data_by_filter(pilih_tempat):
    # ... fungsi get_data lu ...
    return pd.DataFrame({'nama': ['Andi', 'Budi'], 'status_penilaian': ['Sudah', 'Belum'], 'kuadran_kinerja': ['baik', 'kurang']})

# Filter (Tanpa Sidebar, taruh di tengah)
list_unit = get_list_unit()
pilih_tempat = st.selectbox("Pilih Perangkat Daerah:", ["-- Pilih --"] + list_unit)

if pilih_tempat != "-- Pilih --":
    df = get_data_by_filter(pilih_tempat)
    
    # Tombol Download Full Width biar enak dipencet
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    st.download_button("📥 Download Excel", buffer.getvalue(), f"Data_{pilih_tempat}.xlsx", use_container_width=True)
    
    st.write("---")

    # Bar Chart
    st.subheader("Distribusi Kinerja")
    # ... (kodingan fig px.bar lu) ...
    
    # Cards
    c1, c2, c3 = st.columns(3)
    c1.markdown('<div class="metro-card" style="background:#28a745"><b>SUDAH</b><br><h1>10</h1></div>', unsafe_allow_html=True)
    c2.markdown('<div class="metro-card" style="background:#fd7e14"><b>BELUM</b><br><h1>5</h1></div>', unsafe_allow_html=True)
    c3.markdown('<div class="metro-card" style="background:#6c757d"><b>BLANK</b><br><h1>2</h1></div>', unsafe_allow_html=True)
    
    st.write("---")
    
    # Tabel
    st.subheader("Detail Karyawan")
    st.markdown(df[['nama', 'status_penilaian']].to_html(classes="custom-table", index=False, header=["NAMA", "STATUS PENILAIAN"]), unsafe_allow_html=True)
