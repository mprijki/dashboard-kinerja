import streamlit as st
import pandas as pd
import plotly.express as px
import io
import os
from supabase import create_client

# Setup Koneksi
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Dashboard Kinerja", layout="centered")

# CSS Styling - Final Boss Fix (Anti-Keyboard)
st.markdown("""
<style>
    /* 1. Sembunyiin Header Streamlit */
    [data-testid="stHeader"] { display: none; }
    
    /* 2. Tarik container ke atas biar gak ada gap */
    .block-container { 
        padding-top: 0.5rem !important; 
        padding-bottom: 1rem !important;
    }
    
    /* 3. BUNUH fungsi input selectbox biar kibot gak nongol */
    [data-baseweb="select"] input { 
        position: absolute !important;
        width: 1px !important;
        height: 1px !important;
        padding: 0 !important;
        margin: -1px !important;
        overflow: hidden !important;
        clip: rect(0, 0, 0, 0) !important;
        border: 0 !important;
    }
    
    /* 4. Header full width */
    .stImage > img { 
        width: 100% !important; 
        height: auto !important; 
        display: block !important; 
        margin: 0 auto !important;
    }
    
    /* 5. Metro Card */
    .metro-card { 
        padding: 10px 5px; border-radius: 12px; color: white; margin-bottom: 10px; font-weight: bold;
        display: flex; flex-direction: column; justify-content: center; align-items: center; height: 80px;
    }
    .metro-card span { font-size: 12px; margin-bottom: 2px; }
    .metro-card b { font-size: 20px; }
    
    /* 6. Tabel */
    .custom-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 10px; }
    .custom-table th { background-color: #add8e6; color: black; padding: 10px; text-align: center; font-weight: 900; border: 1px solid #ddd; }
    .custom-table td { padding: 8px; text-align: center; border: 1px solid #ddd; }
    .legend-box { font-size: 12px; margin-bottom: 15px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# 1. Header
if os.path.exists("header.png"):
    st.image("header.png")
else:
    st.title("📊 Dashboard Kinerja")

# Fungsi Data
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

# Filter
list_unit = get_list_unit()
pilih_tempat = st.selectbox("Pilih Perangkat Daerah:", ["-- Pilih --"] + list_unit)

if pilih_tempat != "-- Pilih --":
    df_filtered = get_data_by_filter(pilih_tempat)
    
    # Download
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_filtered.to_excel(writer, index=False)
    st.download_button("📥 Download Excel", buffer.getvalue(), f"Data_{pilih_tempat}.xlsx", use_container_width=True)
    
    st.write("---")

    # Chart
    st.subheader(f"Distribusi: {pilih_tempat}")
    order_kategori = ['sangat baik', 'baik', 'butuh perbaikan', 'kurang', 'sangat kurang', '0', 'tidak ada data']
    warna_kategori = {'sangat baik': '#007bff', 'baik': '#28a745', 'butuh perbaikan': '#d4ac0d', 'kurang': '#fd7e14', 'sangat kurang': '#f44336', '0': '#566573', 'tidak ada data': '#8b0000'}
    
    counts = df_filtered['kuadran_kinerja'].astype(str).str.lower().value_counts().reindex(order_kategori, fill_value=0).reset_
