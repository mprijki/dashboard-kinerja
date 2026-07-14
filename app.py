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

# CSS Styling (Fixed & Responsive)
st.markdown("""
<style>
    /* Paksa header gambar biar rapi dan gak meluber */
    .header-img-local { width: 100%; max-width: 300px; display: block; margin: 0 auto 15px auto; }
    .metro-card { padding: 15px; border-radius: 12px; color: white; text-align: center; margin-bottom: 10px; font-weight: bold; }
    .custom-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 10px; }
    .custom-table th { background-color: #add8e6; color: black; padding: 10px; text-align: center; font-weight: 900; border: 1px solid #ddd; }
    .custom-table td { padding: 8px; text-align: center; border: 1px solid #ddd; }
    .legend-box { font-size: 12px; margin-bottom: 15px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# --- 1. Header Panggil File Lokal ---
# Streamlit bakal cari 'header.png' di folder yang sama dengan app.py
if os.path.exists("header.png"):
    st.image("header.png", use_container_width=False, width=300)
else:
    st.title("📊 Dashboard Kinerja")

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
    
    counts = df_filtered['kuadran_kinerja'].astype(str).str.lower().value_counts().reindex(order_kategori, fill_value=0).reset_index()
    counts.columns = ['Kuadran', 'Total']
    
    fig = px.bar(counts, x='Kuadran', y='Total', color='Kuadran', color_discrete_map=warna_kategori)
    fig.update_layout(showlegend=False, xaxis={'showticklabels': False}, margin=dict(t=10, b=10, l=10, r=10))
    st.plotly_chart(fig, use_container_width=True)
    
    # Legend Manual
    st.markdown('<div class="legend-box">🔵 Sangat Baik | 🟢 Baik | 🟡 Perbaikan<br>🟠 Kurang | 🔴 Sangat Kurang | 🔘 Blank</div>', unsafe_allow_html=True)
    
    # Cards
    df_filtered['status_clean'] = df_filtered['status_penilaian'].astype(str).str.lower().str.strip()
    s = df_filtered['status_clean'].value_counts()
    c1, c2, c3 = st.columns(3)
    c1.markdown(f'<div class="metro-card" style="background:#28a745">SUDAH<br><h1>{s.get("sudah", 0)}</h1></div>', unsafe_allow_html=True)
    c2.markdown(f'<div class="metro-card" style="background:#fd7e14">BELUM<br><h1>{s.get("belum", 0)}</h1></div>', unsafe_allow_html=True)
    c3.markdown(f'<div class="metro-card" style="background:#6c757d">BLANK<br><h1>{s.get("tidak ada data", 0)}</h1></div>', unsafe_allow_html=True)
    
    st.write("---")
    
    # Tabel
    st.subheader("Detail Karyawan")
    df_tampil = df_filtered[['nama', 'status_penilaian']].dropna(subset=['nama'])
    st.markdown(df_tampil.to_html(classes="custom-table", index=False, header=["NAMA", "STATUS PENILAIAN"]), unsafe_allow_html=True)
else:
    st.info("Pilih Perangkat Daerah di atas.")
