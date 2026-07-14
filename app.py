# 1. BAR CHART (7 Batang Kinerja - Bersih & Legend di bawah)
    st.subheader(f"Distribusi Kinerja: {pilih_tempat}")
    
    order_kategori = ['sangat baik', 'baik', 'butuh perbaikan', 'kurang', 'sangat kurang', '0', 'tidak ada data']
    
    warna_kategori = {
        'sangat baik': '#007bff',
        'baik': '#28a745',
        'butuh perbaikan': '#d4ac0d',
        'kurang': '#fd7e14',
        'sangat kurang': '#f44336',
        '0': '#566573',
        'tidak ada data': '#8b0000'
    }
    
    counts = df_filtered['kuadran_kinerja'].astype(str).str.lower().value_counts().reindex(order_kategori, fill_value=0).reset_index()
    counts.columns = ['Kuadran', 'Total']
    
    fig = px.bar(counts, x='Kuadran', y='Total', color='Kuadran', color_discrete_map=warna_kategori)
    
    fig.update_layout(
        xaxis={'categoryorder':'array', 'categoryarray':order_kategori},
        showlegend=True,  # Ini diaktifkan
        legend=dict(
            orientation="h",   # Posisi legend horizontal (mendatar)
            yanchor="top",
            y=-0.3,            # Di bawah grafik
            xanchor="center",
            x=0.5
        ),
        margin=dict(t=30, b=50, l=0, r=0) # Margin bawah ditambahin biar legend gak kepotong
    )
    
    st.plotly_chart(fig, use_container_width=True)
