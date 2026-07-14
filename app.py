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

# CSS Styling untuk UI Card Metro
st.markdown("""
<style>
    .metro-card { padding: 20px; border-radius: 15px; color: white; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.2); margin-bottom: 10px; }
    .grad-sudah { background: linear-gradient(135deg, #28a745, #20c997); }
    .grad-belum { background: linear-gradient(135deg, #fd7e14, #ffc107); }
    .grad-none { background: linear-gradient(135deg, #6c757d, #adb5bd); }
</style>
""", unsafe_allow_html=True)

st.title("📊 Dashboard Kinerja Triwulan - 2026")

# Fungsi Data (Paginasi)
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

# Sidebar
list_unit = get_list_unit()
pilih_tempat = st.sidebar.selectbox("Pilih Perangkat Daerah:", options=["-- Pilih --"] + list_unit)

if pilih_tempat != "-- Pilih --":
    df_filtered = get_data_by_filter(pilih_tempat)
    
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
    fig.update_layout(
        xaxis={'categoryorder':'array', 'categoryarray':order_kategori},
        showlegend=True,
        legend=dict(orientation="h", yanchor="top", y=-0.3, xanchor="center", x=0.5),
        margin=dict(t=30, b=50, l=0, r=0)
    )
    st.plotly_chart(fig, use_container_width=True)
    
    st.write("---")
    
    # 2. Kartu Gradien
    st.subheader("Status Penilaian")
    df_filtered['status_clean'] = df_filtered['status_penilaian'].astype(str).str.lower().str.strip()
    s = df_filtered['status_clean'].value_counts()
    
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="metro-card grad-sudah"><h3>SUDAH</h3><h1>{s.get("sudah", 0)}</h1></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metro-card grad-belum"><h3>BELUM</h3><h1>{s.get("belum", 0)}</h1></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metro-card grad-none"><h3>TIDAK ADA</h3><h1>{s.get("tidak ada data", 0)}</h1></div>', unsafe_allow_html=True)
    
    st.write("---")
    
    # 3. Tabel Detail
    st.subheader("Detail Karyawan")
    st.dataframe(df_filtered[['nama', 'unit_kerja', 'status_penilaian', 'kuadran_kinerja']], use_container_width=True)
    
    # 4. Download
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_filtered.to_excel(writer, index=False)
    st.download_button("📥 Download Data Detail (.xlsx)", buffer.getvalue(), f"Data_{pilih_tempat}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
else:
    st.info("Silakan pilih 'Perangkat Daerah' di sidebar.")
