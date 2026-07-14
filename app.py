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
    response = supabase.table("data_triwulan").select("*").range(0, 49999).execute()
    return pd.DataFrame(response.data)

df = get_data()

# 2. Sidebar Filter
st.sidebar.header("Filter Data")
opsi_tempat = sorted(df['unit_kerja'].unique().tolist())
pilih_tempat = st.sidebar.selectbox("Pilih Perangkat Daerah:", options=["-- Pilih --"] + opsi_tempat)

# 3. Logika Tampil Data
if pilih_tempat != "-- Pilih --":
    # Filter data
    df_filtered = df[df['unit_kerja'] == pilih_tempat]
    
    # --- BAGIAN RINGKASAN (REKAP) ---
    st.subheader(f"Ringkasan Kinerja: {pilih_tempat}")
    
    # Hitung total dan breakdown peringkat
    total_karyawan = len(df_filtered)
    rekap = df_filtered['kuadran_kinerja'].value_counts().reindex(
        ['sangat baik', 'baik', 'butuh perbaikan', 'kurang', 'sangat kurang'], fill_value=0
    )
    
    # Tampilkan Metrik Total dulu biar gede
    st.metric("Total pegawai", total_karyawan)
    
    # Tampilkan Rekap Peringkat biar rapi (horizontal)
    cols = st.columns(5)
    peringkat_list = ['sangat baik', 'baik', 'butuh perbaikan', 'kurang', 'sangat kurang']
    for i, p in enumerate(peringkat_list):
        cols[i].metric(p.title(), rekap[p])

    st.sidebar.write(f"Total baris di database: {len(df)}")
    
    st.write("---")
    
    # --- BAGIAN DETAIL TABEL ---
    st.subheader("Detail Karyawan")
    kolom_tampil = ['nama', 'unit_kerja', 'status_penilaian']
    st.dataframe(df_filtered[kolom_tampil], use_container_width=True)
    
else:
    st.info("Silakan pilih 'Perangkat Daerah' di sidebar untuk mulai melihat data.")
