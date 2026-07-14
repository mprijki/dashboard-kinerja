import streamlit as st
from supabase import create_client

# 1. Setup Koneksi ke Supabase
# Kita panggil kuncinya dari Secrets Streamlit (SUPABASE_URL & SUPABASE_KEY)
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase = create_client(url, key)

st.title("Kinerja Triwulan - 2026")

# 2. Fungsi buat narik data dari Supabase
def get_data():
    # Ganti 'nama_tabel_lu' dengan nama tabel asli di database lu
    response = supabase.table("data_triwulan").select("*").execute()
    return response.data

# 3. Nampilin datanya
if st.button("Tampilkan Data"):
    data = get_data()
    st.dataframe(data)
