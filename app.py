import streamlit as st
import pandas as pd
from supabase import create_client

# Setup Koneksi
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Dashboard Kinerja", layout="wide")
st.title("Dashboard Kinerja Triwulan - 2026")

@st.cache_data
def get_data():
    # Narik semua data
    response = supabase.table("data_triwulan").select("*").execute()
    return pd.DataFrame(response.data)

df = get_data()

# 2. Sidebar Filter
st.sidebar.header("Filter Data")

# Filter khusus Tempat Kerja
opsi_tempat = sorted(df['unit_kerja'].unique().tolist())
pilih_tempat = st.sidebar.selectbox("Pilih Perangkat Daerah:", options=["-- Pilih --"] + opsi_tempat)

# 3. Logika Tampil Tabel
if pilih_tempat != "-- Pilih --":
    # Filter data berdasarkan tempat kerja yang dipilih
    df_filtered = df[df['unit_kerja'] == pilih_tempat]
    
    # Pilih kolom yang mau ditampilkan aja
    kolom_tampil = ['nama', 'unit_kerja', 'status_penilaian']
    
    # Metrik Ringkasan (Rekap peringkat_kerja)
    st.subheader(f"Ringkasan Kinerja: {pilih_tempat}")
    
    # Bikin rekap hitungan per peringkat
    rekap = df_filtered['kuadran_kinerja'].value_counts().reset_index()
    rekap.columns = ['Peringkat', 'Jumlah']
    st.table(rekap) # Tabel rekap di atas
    
    # Tampilkan tabel utama (cuma kolom yang diminta)
    st.subheader("Detail Data")
    st.dataframe(df_filtered[kolom_tampil], use_container_width=True)
    
else:
    st.info("Silakan pilih 'Tempat Kerja' di sidebar untuk menampilkan data.")
