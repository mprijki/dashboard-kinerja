import streamlit as st
import pandas as pd
from supabase import create_client

# Setup Koneksi
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Dashboard Kinerja", layout="wide")
st.title("Dashboard Kinerja Triwulan - 2026")

# 1. Fungsi buat narik DAFTAR unit kerja saja (biar enteng)
@st.cache_data
def get_list_unit():
    # Cuma narik kolom unik 'unit_kerja' biar cepet
    response = supabase.table("data_triwulan").select("unit_kerja").execute()
    df_temp = pd.DataFrame(response.data)
    return sorted(df_temp['unit_kerja'].unique().tolist())

# 2. Fungsi buat narik data spesifik per unit
@st.cache_data
def get_data_by_filter(pilih_tempat):
    response = supabase.table("data_triwulan") \
        .select("*") \
        .eq("unit_kerja", pilih_tempat) \
        .execute()
    return pd.DataFrame(response.data)

# Sidebar
st.sidebar.header("Filter Data")
list_unit = get_list_unit()
pilih_tempat = st.sidebar.selectbox("Pilih Perangkat Daerah:", options=["-- Pilih --"] + list_unit)

# 3. Logika Tampil Data
if pilih_tempat != "-- Pilih --":
    # Panggil data spesifik
    df_filtered = get_data_by_filter(pilih_tempat)
    
    st.subheader(f"Ringkasan Kinerja: {pilih_tempat}")
    
    # Hitung total dan rekap peringkat
    total_karyawan = len(df_filtered)
    rekap = df_filtered['kuadran_kinerja'].value_counts().reindex(
        ['sangat baik', 'baik', 'butuh perbaikan', 'kurang', 'sangat kurang'], fill_value=0
    )
    
    st.metric("Total Pegawai", total_karyawan)
    
    cols = st.columns(5)
    peringkat_list = ['sangat baik', 'baik', 'butuh perbaikan', 'kurang', 'sangat kurang']
    for i, p in enumerate(peringkat_list):
        cols[i].metric(p.title(), rekap[p])

    st.write("---")
    
    # Detail Tabel
    st.subheader("Detail Karyawan")
    kolom_tampil = ['nama', 'unit_kerja2', 'status_penilaian']
    st.dataframe(df_filtered[kolom_tampil], use_container_width=True)
    
else:
    st.info("Silakan pilih 'Perangkat Daerah' di sidebar untuk mulai melihat data.")
