import streamlit as st
import pandas as pd
import plotly.express as px
import io
from supabase import create_client

# Setup Koneksi
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.set_page_config(page_title="Dashboard Kinerja", layout="centered")

# CSS Styling (Fixed & Responsive)
st.markdown("""
<style>
    .img-center { display: flex; justify-content: center; margin-bottom: 20px; }
    .metro-card { padding: 10px; border-radius: 8px; color: white; text-align: center; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
    
    /* Tabel Murni HTML biar gak berantakan */
    .custom-table { width: 100%; border-collapse: collapse; margin-top: 10px; }
    .custom-table th { background-color: #add8e6 !important; padding: 12px; text-align: center; font-weight: bold; border: 1px solid #ddd; }
    .custom-table td { padding: 8px; text-align: center; border: 1px solid #ddd; }
</style>
""", unsafe_allow_html=True)

# 1. Header Gambar
st.markdown('<div class="img-center">', unsafe_allow_html=True)
try:
    st.image("header.png", width=300)
except:
    st.title("📊 Dashboard Kinerja - 2026")
st.markdown('</div>', unsafe_allow_html=True)

# Fungsi Data (Paginasi)
@st.cache_data(ttl=3600)
def get_list_unit():
    # Placeholder logic (ganti sesuai fungsi asli lu)
    return sorted(["Unit A", "Unit B", "Unit C"])

@st.cache_data(ttl=3600)
def get_data_by_filter(pilih_tempat):
    # Dummy data
    return pd.DataFrame({'nama': ['Andi', 'Budi'], 'status_penilaian': ['Sudah', 'Belum'], 'kuadran_kinerja': ['baik', 'kurang']})

# Filter
list_unit = get_list_unit()
col1, col2 = st.columns([3, 1])
pilih_tempat = col1.selectbox("Pilih Perangkat Daerah:", ["-- Pilih --"] + list_unit)

if pilih_tempat != "-- Pilih --":
    df = get_data_by_filter(pilih_tempat)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, index=False)
    col2.download_button("📥 Excel", buffer.getvalue(), f"Data_{pilih_tempat}.xlsx", use_container_width=True)
    
    st.write("---")

    # 1. Chart
    st.subheader("Distribusi Kinerja")
    fig = px.bar(df['kuadran_kinerja'].value_counts().reset_index(), x='kuadran_kinerja', y='count')
    fig.update_layout(xaxis={'showticklabels': False}, margin=dict(t=0, b=50, l=0, r=0))
    st.plotly_chart(fig, use_container_width=True)
    
    # 2. Cards
    c1, c2, c3 = st.columns(3)
    c1.markdown('<div class="metro-card" style="background:#28a745">SUDAH<br><b>10</b></div>', unsafe_allow_html=True)
    c2.markdown('<div class="metro-card" style="background:#fd7e14">BELUM<br><b>5</b></div>', unsafe_allow_html=True)
    c3.markdown('<div class="metro-card" style="background:#6c757d">BLANK<br><b>2</b></div>', unsafe_allow_html=True)
    
    st.write("---")
    
    # 3. Tabel Custom (Anti-Berantakan)
    st.subheader("Detail Karyawan")
    # Pake to_html buat render tabel sendiri
    df_tampil = df[['nama', 'status_penilaian']]
    st.markdown(df_tampil.to_html(classes="custom-table", index=False, header=["NAMA", "STATUS PENILAIAN"]), unsafe_allow_html=True)

else:
    st.info("Pilih Perangkat Daerah di atas.")
