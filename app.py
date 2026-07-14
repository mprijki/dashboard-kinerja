import streamlit as st
import pandas as pd
from supabase import create_client

# Setup Koneksi
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Dashboard Kinerja", layout="wide")
st.title("📊 Dashboard Kinerja Triwulan - 2026")

@st.cache_data
def get_data():
    response = supabase.table("data_triwulan").select("*").execute()
    return pd.DataFrame(response.data)

df = get_data()

# 2. Sidebar Filter (Sudah disesuaikan dengan kolom asli lu)
st.sidebar.header("Filter Data")

# Dropdown buat milih kolom apa yang mau difilter
pilihan_kolom = ["unit_kerja", "hasil_kerja", "perilaku_kerja", "kuadran_kinerja", "status_penilaian"]
kolom_filter = st.sidebar.selectbox("Pilih Kategori untuk Filter:", options=pilihan_kolom)

# Multiselect buat milih isi dari kolom tersebut
nilai_filter = st.sidebar.multiselect(f"Pilih {kolom_filter}:", options=df[kolom_filter].unique())

if nilai_filter:
    df_filtered = df[df[kolom_filter].isin(nilai_filter)]
else:
    df_filtered = df

# 3. Metrik Ringkasan
col1, col2 = st.columns(2)
col1.metric("Total Data", len(df_filtered))

# Karena 'peringkat_kerja' ada isinya (sangat okeh, dll), 
# kita hitung berapa banyak yang 'sangat okeh' sebagai contoh metrik
if 'kuadran_kinerja' in df_filtered.columns:
    jumlah_sangat_okeh = len(df_filtered[df_filtered['kuadran_kinerja'] == 'sangat baik'])
    col2.metric("Total Sangat Okeh", jumlah_sangat_okeh)

# 4. Tampilkan Tabel
st.subheader("Tabel Data")
st.dataframe(df_filtered, use_container_width=True)
