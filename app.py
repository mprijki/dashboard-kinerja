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

# CSS Styling - Final Clean
st.markdown("""
<style>
    [data-testid="stHeader"] { display: none; }
    .block-container { padding-top: 0.5rem !important; padding-bottom: 1rem !important; }
    
    .stImage > img { width: 100% !important; height: auto !important; display: block !important; margin: 0 auto !important; }
    
    /* Metro Card */
    .metro-card { 
        padding: 10px 5px; border-radius: 12px; color: white; margin-bottom: 10px; font-weight: bold;
        display: flex; flex-direction: column; justify-content: center; align-items: center; height: 80px;
    }
    
    /* Tabel Header Rapi & Uppercase */
    .custom-table { width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 10px; }
    .custom-table th { 
        background-color: #add8e6; color: black; padding: 10px; text-align: center; 
        font-weight: 900; border: 1px solid #ddd; text-transform: uppercase !important; 
    }
    .custom-table td { padding: 8px; text-align: center; border: 1px solid #ddd; }
    .legend-box { font-size: 12px; margin-bottom: 15px; text-align: center; }
</style>
""", unsafe_allow_html=True)

# 1. Header
if os.path.exists("header.png"): st.image("header.png")
else: st.title("📊 Dashboard Kinerja")

# Fungsi Data
@st.cache_data(ttl=3600)
def get_list_unit():
    try:
        response = supabase.table("data_triwulan").select("unit_kerja").execute()
        return sorted(list(set([item['unit_kerja'] for item in response.data])))
    except: return []

@st.cache_data(ttl=3600)
def get_data_by_filter(pilih_tempat):
    try:
        response = supabase.table("data_triwulan").select("*").eq("unit_kerja", pilih_tempat).execute()
        return pd.DataFrame(response.data)
    except: return pd.DataFrame()

# Filter
list_unit = get_list_unit()
pilih_tempat = st.selectbox("Pilih Perangkat Daerah:", ["-- Pilih --"] + list_unit)

if pilih_tempat != "-- Pilih --":
    df_filtered = get_data_by_filter(pilih_tempat)
    
    if not df_filtered.empty and 'kuadran_kinerja' in df_filtered.columns:
        # Siapkan df_tampil yang rapi
        df_tampil = df_filtered[['nama', 'status_penilaian']].copy()
        df_tampil.columns = ["NAMA", "STATUS PENILAIAN"]
        
        # Download (Sekarang pake df_tampil biar cuma 2 kolom)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_tampil.to_excel(writer, index=False)
        st.download_button("📥 Download Excel", buffer.getvalue(), f"Data_{pilih_tempat}.xlsx", use_container_width=True)
        
        st.write("---")

        # Chart
        st.subheader(f"Distribusi: {pilih_tempat}")
        order_kategori = ['sangat baik', 'baik', 'butuh perbaikan', 'kurang', 'sangat kurang', '0', 'tidak ada data']
        counts = df_filtered['kuadran_kinerja'].astype(str).str.lower().value_counts().reindex(order_kategori, fill_value=0).reset_index()
        counts.columns = ['Kuadran', 'Total']
        
        fig = px.bar(counts, x='Kuadran', y='Total', color='Kuadran', 
                     color_discrete_map={'sangat baik': '#007bff', 'baik': '#28a745', 'butuh perbaikan': '#d4ac0d', 
                                         'kurang': '#fd7e14', 'sangat kurang': '#f44336', '0': '#566573', 'tidak ada data': '#8b0000'})
        fig.update_layout(showlegend=False, xaxis=dict(title=None, showticklabels=False), yaxis=dict(title=None), margin=dict(t=10, b=10, l=10, r=10))
        st.plotly_chart(fig, use_container_width=True)
        
        # Legend
        st.markdown('<div class="legend-box">🔵 Sangat Baik | 🟢 Baik | 🟡 Perbaikan<br>🟠 Kurang | 🔴 Sangat Kurang | 🔘 Blank</div>', unsafe_allow_html=True)
        
        # Cards
        df_filtered['status_clean'] = df_filtered['status_penilaian'].astype(str).str.lower().str.strip()
        s = df_filtered['status_clean'].value_counts()
        c1, c2, c3 = st.columns(3)
        c1.markdown(f'<div class="metro-card" style="background:#28a745"><span>SUDAH</span><b>{s.get("sudah", 0)}</b></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metro-card" style="background:#fd7e14"><span>BELUM</span><b>{s.get("belum", 0)}</b></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metro-card" style="background:#6c757d"><span>BLANK</span><b>{s.get("tidak ada data", 0)}</b></div>', unsafe_allow_html=True)
        
        st.write("---")
        
        # Tabel
        st.subheader("Detail Karyawan")
        st.markdown(df_tampil.to_html(classes="custom-table", index=False), unsafe_allow_html=True)
    else:
        st.info("Data tidak ditemukan atau kosong.")
else:
    st.info("Pilih Perangkat Daerah di atas.")
