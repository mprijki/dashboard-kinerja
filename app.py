import streamlit as st
import pandas as pd
import plotly.express as px
import io
from supabase import create_client

# Setup Koneksi
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Dashboard Kinerja", layout="wide")

# CSS Styling Total & Responsive
st.markdown("""
<style>
    .metro-card { padding: 15px; border-radius: 10px; color: white; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 10px; }
    .grad-sudah { background: linear-gradient(135deg, #28a745, #20c997); }
    .grad-belum { background: linear-gradient(135deg, #fd7e14, #ffc107); }
    .grad-none { background: linear-gradient(135deg, #6c757d, #adb5bd); }
    
    /* Header Tabel Bold & Rata Tengah */
    .stDataFrame thead tr th { 
        text-align: center !important; 
        font-weight: bold !important; 
        background-color: #add8e6 !important; 
        color: black !important;
    }
    /* Biar isi tabel rata tengah juga */
    .stDataFrame tbody td { text-align: center !important; }
</style>
""", unsafe_allow_html=True)

# 1. Header Gambar
try:
    st.image("header.png", width=250)
except:
    st.title("📊 Dashboard Kinerja Triwulan - 2026")

# Fungsi Data (Paginasi Asli)
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
col1, col2 = st.columns([3, 1])
pilih_tempat = col1.selectbox("Pilih Perangkat Daerah:", options=["-- Pilih --"] + list_unit)

if pilih_tempat != "-- Pilih --":
    df_filtered = get_data_by_filter(pilih_tempat)
    
    # Download
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_filtered.to_excel(writer, index=False)
    col2.download_button("📥 Excel", buffer.getvalue(), f"Data_{pilih_tempat}.xlsx", use_container_width=True)
    
    st.write("---")

    # 1. BAR CHART
    st.subheader(f"Distribusi Kinerja: {pilih_tempat}")
    order_kategori = ['sangat baik', 'baik', 'butuh perbaikan', 'kurang', 'sangat kurang', '0', 'tidak ada data']
    warna_kategori = {
        'sangat baik': '#007bff', 'baik': '#28a745', 'butuh perbaikan': '#d4ac0d',
        'kurang': '#fd7e14', 'sangat kurang': '#f44336', '0': '#566573', 'tidak ada data': '#8b0000'
    }
    counts = df_filtered['kuadran_kinerja'].astype(str).str.lower().value_counts().reindex(order_kategori, fill_value=0).reset_index()
    counts.columns = ['Kuadran', 'Total']
    
    fig = px.bar(counts, x='Kuadran', y='Total', color='Kuadran', color_discrete_map=warna_kategori)
    fig.update_layout(xaxis={'showticklabels': False}, showlegend=True, legend=dict(orientation="h", yanchor="top", y=-0.2, xanchor="center", x=0.5), margin=dict(t=30, b=50, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)
    
    # 2. Kartu
    df_filtered['status_clean'] = df_filtered['status_penilaian'].astype(str).str.lower().str.strip()
    s = df_filtered['status_clean'].value_counts()
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="metro-card grad-sudah"><b>SUDAH</b><br><h1>{s.get("sudah", 0)}</h1></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metro-card grad-belum"><b>BELUM</b><br><h1>{s.get("belum", 0)}</h1></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metro-card grad-none"><b>BLANK</b><br><h1>{s.get("tidak ada data", 0)}</h1></div>', unsafe_allow_html=True)
    
    st.write("---")
    
    # 3. Tabel Responsive
    st.subheader("Detail Karyawan")
    df_tampil = df_filtered[['nama', 'status_penilaian']].dropna(subset=['nama'])
    df_tampil.columns = ['NAMA', 'STATUS PENILAIAN']
    # Pake st.dataframe biar responsif di HP
    st.dataframe(df_tampil, use_container_width=True, hide_index=True)

else:
    st.info("Silakan pilih Perangkat Daerah di atas.")
