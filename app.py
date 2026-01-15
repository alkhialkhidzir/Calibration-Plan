import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime
import calendar

st.set_page_config(page_title="Dashboard Kalibrasi", layout="wide")

st.markdown("""
<style>

/* ====== GLOBAL ====== */
html, body, [class*="css"]  {
    font-family: 'Segoe UI', sans-serif;
    background-color: #f5f6f8;
    color: #1f2937;
}

/* ====== SIDEBAR ====== */
section[data-testid="stSidebar"] {
    background-color: #eef0f3;
    border-right: 1px solid #d1d5db;
}

section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] label {
    color: #1f2937 !important;
}

/* Button sidebar */
section[data-testid="stSidebar"] .stButton>button {
    background-color: #e5e7eb;
    border-radius: 10px;
    color: #1f2937;
    font-weight: 600;
    border: 1px solid #d1d5db;
    padding: 12px;
}

section[data-testid="stSidebar"] .stButton>button:hover {
    background-color: #d1d5db;
}

/* ====== HERO HEADER ====== */
.hero {
    background: linear-gradient(90deg, #f3f4f6, #e5e7eb);
    padding: 40px;
    border-radius: 20px;
    text-align: center;
    margin-bottom: 30px;
    border: 1px solid #d1d5db;
}

.hero h1 {
    font-size: 40px;
    margin-bottom: 10px;
    color: #1f2937;
}

.hero p {
    font-size: 16px;
    color: #4b5563;
}

/* ====== CARD ====== */
.card {
    background-color: #ffffff;
    padding: 25px;
    border-radius: 16px;
    box-shadow: 0 4px 14px rgba(0,0,0,0.06);
    margin-bottom: 25px;
    border: 1px solid #e5e7eb;
}

/* ====== METRIC ====== */
div[data-testid="metric-container"] {
    background-color: #ffffff;
    padding: 20px;
    border-radius: 14px;
    border: 1px solid #e5e7eb;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

/* ====== DATAFRAME ====== */
.stDataFrame {
    border-radius: 14px;
    overflow: hidden;
    border: 1px solid #e5e7eb;
}

</style>
""", unsafe_allow_html=True)


# ====== Fungsi Utility ======
def load_excel(file):
    """Load semua sheet dari Excel file"""
    xls = pd.ExcelFile(file)
    data = {}
    for sheet in xls.sheet_names:
        df = pd.read_excel(file, sheet_name=sheet)
        data[sheet] = df
    return data

def get_month_name(date_str):
    """Ekstrak nama bulan dari tanggal"""
    try:
        date_obj = pd.to_datetime(date_str)
        return date_obj.strftime('%B').upper()
    except:
        return None

def get_year(date_str):
    """Ekstrak tahun dari tanggal"""
    try:
        date_obj = pd.to_datetime(date_str)
        return str(date_obj.year)
    except:
        return None

def filter_by_month_year(df, bulan=None, tahun=None):
    """Filter dataframe berdasarkan bulan dan tahun dari TANGGAL PLAN"""
    df_filtered = df.copy()
    
    if bulan or tahun:
        df_filtered['BULAN'] = df_filtered['TANGGAL PLAN'].apply(get_month_name)
        df_filtered['TAHUN'] = df_filtered['TANGGAL PLAN'].apply(get_year)
        
        if bulan and bulan != 'SEMUA':
            df_filtered = df_filtered[df_filtered['BULAN'] == bulan]
        if tahun and tahun != 'SEMUA':
            df_filtered = df_filtered[df_filtered['TAHUN'] == tahun]
        
        # Drop kolom temporary
        df_filtered = df_filtered.drop(['BULAN', 'TAHUN'], axis=1)
    
    return df_filtered

def update_status(row):
    """Update status berdasarkan tanggal realisasi vs expected"""
    real = row['TANGGAL REALISASI']
    exp = row['TANGGAL EXP']
    
    if pd.isna(real) or real == '' or real == '-':
        return "⏳ Belum"
    
    try:
        real_date = pd.to_datetime(real)
        exp_date = pd.to_datetime(exp)
        
        if real_date <= exp_date:
            return "✅ Tepat Waktu"
        else:
            return "⚠️ Terlambat"
    except:
        return "⏳ Belum"

def color_status_row(row):
    """Styling untuk baris berdasarkan status"""
    if row['STATUS'] == "✅ Tepat Waktu":
        return ['background-color: #d4edda'] * len(row)
    elif row['STATUS'] == "⚠️ Terlambat":
        return ['background-color: #f8d7da'] * len(row)
    else:
        return ['background-color: #fff3cd'] * len(row)

# ====== Inisialisasi Session State ======
if 'data_dict' not in st.session_state:
    st.session_state.data_dict = None
if 'current_data' not in st.session_state:
    st.session_state.current_data = None

# ====== Sidebar ======
with st.sidebar:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.image("garudafood_logo.png", width=220)

    uploaded_file = st.file_uploader("📁 Upload File Excel", type=["xlsx", "xls"])
    
    if uploaded_file:
        # Load data saat pertama kali upload
        if st.session_state.data_dict is None:
            st.session_state.data_dict = load_excel(uploaded_file)
            st.success("✅ File berhasil diupload!")
        
        data_dict = st.session_state.data_dict
        
        # Filter
        st.subheader("Filter Data")
        sheet_name = st.selectbox("Jenis Mesin", list(data_dict.keys()))
        
        # Get unique years and months dari TANGGAL PLAN
        df_original = data_dict[sheet_name].copy()
        df_original['TEMP_MONTH'] = df_original['TANGGAL PLAN'].apply(get_month_name)
        df_original['TEMP_YEAR'] = df_original['TANGGAL PLAN'].apply(get_year)
        
        available_years = ['SEMUA'] + sorted(df_original['TEMP_YEAR'].dropna().unique().tolist())
        available_months = ['SEMUA'] + sorted(df_original['TEMP_MONTH'].dropna().unique().tolist(), 
                                               key=lambda x: list(calendar.month_name).index(x.title()) if x.title() in calendar.month_name else 0)
        
        tahun = st.selectbox("Tahun", available_years)
        bulan = st.selectbox("Bulan", available_months)

# ====== Main Content ======
if uploaded_file and st.session_state.data_dict:
    df = data_dict[sheet_name].copy()

    df['TANGGAL PLAN'] = pd.to_datetime(df['TANGGAL PLAN']).dt.date
    df['TANGGAL EXP'] = pd.to_datetime(df['TANGGAL EXP']).dt.date

    if 'TANGGAL REALISASI' in df.columns:
        df['TANGGAL REALISASI'] = pd.to_datetime(df['TANGGAL REALISASI']).dt.date

    # Apply filters
    df_filtered = filter_by_month_year(df, 
                                        bulan if bulan != 'SEMUA' else None,
                                        tahun if tahun != 'SEMUA' else None)
    
    
    # Hitung status
    df_filtered['STATUS'] = df_filtered.apply(update_status, axis=1)
    
    # Header dengan metrics
    st.markdown(f"""
    <div class="hero">
        <h1>Dashboard Kalibrasi</h1>
        <p>Monitoring • Performance • Compliance</p>
    </div>
    """, unsafe_allow_html=True)
    
    filter_info = []
    if tahun != 'SEMUA':
        filter_info.append(f"Tahun: {tahun}")
    if bulan != 'SEMUA':
        filter_info.append(f"Bulan: {bulan}")
    
    if filter_info:
        st.caption(" | ".join(filter_info))
    
    st.markdown("---")
    
    # Metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_mesin = len(df_filtered)
    status_counts = df_filtered['STATUS'].value_counts()
    tepat = status_counts.get('✅ Tepat Waktu', 0)
    terlambat = status_counts.get('⚠️ Terlambat', 0)
    belum = status_counts.get('⏳ Belum', 0)
    
    with col1:
        st.metric("📊 Plan kalibrasi", total_mesin)
    with col2:
        persen_tepat = f"{tepat/total_mesin*100:.1f}%" if total_mesin > 0 else "0%"
        st.metric("✅ Tepat Waktu", tepat, delta=persen_tepat)
    with col3:
        persen_terlambat = f"{terlambat/total_mesin*100:.1f}%" if total_mesin > 0 else "0%"
        st.metric("⚠️ Terlambat", terlambat, delta=persen_terlambat, delta_color="inverse")
    with col4:
        persen_belum = f"{belum/total_mesin*100:.1f}%" if total_mesin > 0 else "0%"
        st.metric("⏳ Belum", belum, delta=persen_belum)
    
    st.markdown("---")

    
    # Tampilkan data
    # st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📋 Data Jadwal Kalibrasi")
    
    # Sortir berdasarkan status (Terlambat > Belum > Tepat Waktu)
    status_order = {"⚠️ Terlambat": 0, "⏳ Belum": 1, "✅ Tepat Waktu": 2}
    df_filtered['SORT_ORDER'] = df_filtered['STATUS'].map(status_order)
    df_filtered = df_filtered.sort_values('SORT_ORDER').drop('SORT_ORDER', axis=1)
    
    # Reset nomor urut agar tetap 1, 2, 3, dst
    df_filtered = df_filtered.reset_index(drop=True)
    df_filtered.insert(0, 'NO_URUT', range(1, len(df_filtered) + 1))
    
    # Drop kolom NO original dan IDENTIFIER yang temporary
    if 'NO' in df_filtered.columns:
        df_filtered = df_filtered.drop('NO', axis=1)
    if 'IDENTIFIER' in df_filtered.columns:
        df_filtered = df_filtered.drop('IDENTIFIER', axis=1)
    
    # Rename NO_URUT jadi NO
    df_filtered = df_filtered.rename(columns={'NO_URUT': 'NO'})
    
    # Styling
    styled_df = df_filtered.style.apply(color_status_row, axis=1)
    st.dataframe(styled_df, use_container_width=True, height=500, hide_index=True)
    
    st.markdown("---")

    # Form input realisasi
    st.subheader("Input Tanggal Realisasi")
    
    with st.form("update_form"):
        col_form1, col_form2, col_form3 = st.columns([3, 2, 1])
        
        with col_form1:
            # Buat identifier yang unik untuk setiap alat
            df_filtered['IDENTIFIER'] = df_filtered.apply(
                lambda row: f"[{row['NO']}] {row['NAMA ALAT']} - {row.get('NO MESIN', row.get('IDENTITAS', ''))}",
                axis=1
            )
            alat_options = df_filtered['IDENTIFIER'].tolist()
            selected_alat = st.selectbox("Pilih Alat", alat_options)
        
        with col_form2:
            tanggal_realisasi = st.date_input("Tanggal Realisasi", datetime.now())
        
        with col_form3:
            st.write("")
            st.write("")
            submit_button = st.form_submit_button("Update", use_container_width=True)
        
        if submit_button and selected_alat:
            # Extract NO dari identifier
            no_alat = int(selected_alat.split(']')[0].replace('[', ''))
            
            # Update di df_filtered
            idx = df_filtered[df_filtered['NO'] == no_alat].index[0]
            df_filtered.loc[idx, 'TANGGAL REALISASI'] = tanggal_realisasi
            
            # Update di data_dict original
            original_idx = df[df['NO'] == no_alat].index[0]
            data_dict[sheet_name].loc[original_idx, 'TANGGAL REALISASI'] = tanggal_realisasi
            
            st.session_state.data_dict = data_dict
            st.success(f"✅ Tanggal realisasi berhasil diupdate!")
            st.rerun()
    
    st.markdown("---")
    
    # Detail per plant/mesin (untuk tracking lebih detail)
    if sheet_name == "BAKING":
        group_col = 'PLANT'
    else:
        group_col = 'PLANT'
    
    if group_col in df_filtered.columns:
        st.subheader(f"Detail per Plant")
        
        summary = df_filtered.groupby(group_col).agg({
            'NO': 'count',
            'STATUS': lambda x: (x == '✅ Tepat Waktu').sum()
        }).rename(columns={'NO': 'Total', 'STATUS': 'Tepat Waktu'})
        
        summary['Belum/Terlambat'] = summary['Total'] - summary['Tepat Waktu']
        summary['% Selesai'] = (summary['Tepat Waktu'] / summary['Total'] * 100).round(1)
        
        st.dataframe(summary, use_container_width=True)
    
    st.markdown("---")
    
    # Download section
    st.subheader("Simpan Data Terbaru")
    
    col_btn = st.columns(1)[0]
    
    with col_btn:
        # Create Excel file untuk download
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            for sheet in data_dict.keys():
                # Hapus kolom STATUS sebelum save (karena kalkulasi dinamis)
                df_to_save = data_dict[sheet].copy()
                if 'STATUS' in df_to_save.columns:
                    df_to_save = df_to_save.drop('STATUS', axis=1)
                df_to_save.to_excel(writer, sheet_name=sheet, index=False)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        st.download_button(
            label="📥 Download",
            data=output.getvalue(),
            file_name=f"kalibrasi_update_{timestamp}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

else:
    # ====== WELCOME SCREEN ======
    st.markdown("""
    <div class="hero">
        <h1>Dashboard Kalibrasi Mesin</h1>
        <p>Monitoring • Performance • Compliance</p>
        <br>
        <p style="font-size:18px;">
            👈 Silakan upload file Excel untuk memulai
        </p>
    </div>
    """, unsafe_allow_html=True)

# ====== FOOTER ======
st.markdown("---")
st.caption(
    "<p style='text-align: center;'>Dashboard Jadwal Kalibrasi GarudaFood © 2026</p>",
    unsafe_allow_html=True
)