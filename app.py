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

# CSS & JS Styling - Final Boss Fix (Anti-Keyboard)
st.markdown("""
<style>
    /* 1. Sembunyiin Header Streamlit */
    [data-testid="stHeader"] { display: none; }
    
    /* 2. Tarik container ke atas biar gak ada gap */
    .block-container { 
        padding-top: 0.5rem !important; 
        padding-bottom: 1rem !important;
    }
    
    /* 3. Mencegah Keyboard muncul di Selectbox */
    [data-baseweb="select"] input { 
        pointer-events: none !important; 
        caret-color: transparent !important; 
        user-select: none !important; 
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

<script>
    // JS buat nambahin atribut readonly ke semua input combobox
    window.onload = function() {
        const checkExist = setInterval(function() {
            const inputs = document.querySelectorAll('input[role="combobox"]');
            if (inputs.length > 0) {
                inputs.forEach(input => {
                    input.setAttribute('readonly', 'true');
                });
                clearInterval(checkExist);
            }
        }, 500);
    };
</script>
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
    
    counts = df_filtered['kuadran_kinerja'].astype(str).str.lower().value_counts().reindex(order_kategori, fill_value=0).reset_index()
    counts.columns = ['Kuadran', 'Total']
    
    fig = px.bar(counts, x='Kuadran', y='Total', color='Kuadran', color_discrete_map=warna_kategori)
    fig.update_layout(
        showlegend=False, 
        xaxis=dict(title=None, showticklabels=False), 
        yaxis=dict(title=None),                      
        margin=dict(t=10, b=10, l=10, r=10)
    )
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
    
    st
