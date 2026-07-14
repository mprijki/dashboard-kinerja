import streamlit as st
import pandas as pd
from supabase import create_client

# Setup Koneksi
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Dashboard Kinerja", layout="wide")
st.title("Dashboard Kinerja Triwulan - 2026")

# 1. Fungsi narik DAFTAR unit kerja (looping 30rb data)
@st.cache_data
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

# 2. Fungsi narik data spesifik per unit (looping buat yang >1000 pegawai)
@st.cache_data
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

# Sidebar
st.sidebar.header("Filter Data")
list_unit = get_list_unit()
pilih_tempat = st.sidebar.selectbox("Pilih Perangkat Daerah:", options=["-- Pilih --"] + list_unit)

# 3. Logika Tampil Data
if pilih_tempat != "-- Pilih --":
    df_filtered = get_data_by_filter(pilih_tempat)
    
    st.subheader(f"Ringkasan Kinerja: {pilih_tempat}")
    
    # Metrik Total
    total_karyawan = len(df_filtered)
    st.metric("Total Pegawai", total_karyawan)
    st.write("---")
    
    # Status Penilaian (Case-insensitive)
    st.subheader("Status Penilaian")
    df_filtered['status_clean'] = df_filtered['status_penilaian'].astype(str).str.lower().str.strip()
    s = df_filtered['status_clean'].value_counts()
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Sudah", s.get('SUDAH', 0))
    c2.metric("Belum", s.get('BELUM', 0))
    c3.metric("Tidak Ada Data", s.get('TIDAK ADA DATA', 0))
    
    st.write("---")
    
    # Distribusi Kinerja
    st.subheader("Distribusi Kinerja")
    k = df_filtered['kuadran_kinerja'].value_counts().reindex(
        ['sangat baik', 'baik', 'butuh perbaikan', 'kurang', 'sangat kurang'], fill_value=0
    )
    cols = st.columns(5)
    labels = ['Sangat Baik', 'Baik', 'Butuh Perbaikan', 'Kurang', 'Sangat Kurang']
    for i, col_name in enumerate(['sangat baik', 'baik', 'butuh perbaikan', 'kurang', 'sangat kurang']):
        cols[i].metric(labels[i], k[col_name])

    st.write("---")
    
    # Detail Tabel
    st.subheader("Detail Karyawan")
    st.dataframe(df_filtered[['nama', 'unit_kerja', 'status_penilaian']], use_container_width=True)
else:
    st.info("Silakan pilih 'Perangkat Daerah' di sidebar untuk mulai melihat data.")
