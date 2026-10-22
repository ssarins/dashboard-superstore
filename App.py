import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO


# JUDUL ATAS
st.title("Dashboard Penjualan Superstore")
st.write(
    "Dashboard interaktif untuk menganalisis penjualan, profit, diskon, "
    "dan pengiriman pada data toko ritel Superstore (Amerika Serikat) "
    "periode 2014-2017. Dataset berasal dari Kaggle. Gunakan filter di "
    "sebelah kiri untuk mengubah KPI, grafik, tabel, dan insight."
)


# BACA DATA (PANDAS)
@st.cache_data
def load_data():
    df = pd.read_csv(
        "superstore_clean.csv",
        parse_dates=["Order Date", "Ship Date"],
        dtype={"Postal Code": str}
    )

    return df

df = load_data()


# BUAT SIDEBAR (FILTER)
st.sidebar.header("Filter Dashboard")


# BATAS TANGGAL
min_date = df["Order Date"].min().date()
max_date = df["Order Date"].max().date()


# DATE PICKER
date_range = st.sidebar.date_input(
    "Periode Order",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date
)

if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date = end_date = date_range


# FILTER REGION
regions = st.sidebar.multiselect(
    "Region",
    sorted(df["Region"].dropna().unique()),
    default=sorted(df["Region"].dropna().unique())
)


# FILTER KATEGORI
categories = st.sidebar.multiselect(
    "Kategori",
    sorted(df["Category"].dropna().unique()),
    default=sorted(df["Category"].dropna().unique())
)


# FILTER SEGMEN PELANGGAN
segments = st.sidebar.multiselect(
    "Segmen Pelanggan",
    sorted(df["Segment"].dropna().unique()),
    default=sorted(df["Segment"].dropna().unique())
)


# FILTERING DATA (PANDAS)
filtered = df[
    (df["Order Date"].dt.date >= start_date) &
    (df["Order Date"].dt.date <= end_date) &
    (df["Region"].isin(regions)) &
    (df["Category"].isin(categories)) &
    (df["Segment"].isin(segments))
].copy()


# CEK DATA HASIL FILTER
if filtered.empty:
    st.warning("Tidak ada data sesuai filter yang dipilih.")
    st.stop()


# HITUNG KPI
total_sales = filtered["Sales"].sum()
total_profit = filtered["Profit"].sum()
total_orders = filtered["Order ID"].nunique()

profit_margin = (
    total_profit / total_sales * 100
    if total_sales > 0 else 0
)

average_shipping = filtered["Shipping_Days"].mean()

loss_transactions = (filtered["Profit"] < 0).sum()

loss_percentage = (
    loss_transactions / len(filtered) * 100
    if len(filtered) > 0 else 0
)


# TAMPILKAN KPI
c1, c2, c3, c4 = st.columns(4)

c1.metric("Total Sales", f"${total_sales:,.0f}")
c2.metric("Total Profit", f"${total_profit:,.0f}")
c3.metric("Jumlah Order", f"{total_orders:,}")
c4.metric("Profit Margin", f"{profit_margin:.1f}%")

c1, c2 = st.columns(2)

c1.metric(
    "Rata-rata Waktu Pengiriman",
    f"{average_shipping:.1f} hari" if pd.notna(average_shipping) else "Tidak tersedia"
)
c2.metric("Transaksi Rugi", f"{loss_percentage:.1f}%")


# MEMBUAT 2 KOLOM GRAFIK
col1, col2 = st.columns(2)


# BUAT LINE CHART (TREN SALES DAN PROFIT BULANAN)
with col1:

    monthly = (
        filtered.groupby("Month", as_index=False)
        .agg(Sales=("Sales", "sum"), Profit=("Profit", "sum"))
        .sort_values("Month")
    )

    fig = px.line(
        monthly,
        x="Month",
        y=["Sales", "Profit"],
        markers=True,
        title="Tren Sales dan Profit Bulanan",
        labels={"value": "Nilai (USD)", "Month": "Bulan", "variable": "Metrik"}
    )

    st.plotly_chart(fig)


# BUAT BAR CHART (SALES PER SUB-KATEGORI)
with col2:

    subcategory_sales = (
        filtered.groupby("Sub-Category", as_index=False)["Sales"]
        .sum()
        .sort_values("Sales", ascending=True)
    )

    fig = px.bar(
        subcategory_sales,
        x="Sales",
        y="Sub-Category",
        orientation="h",
        title="Sales per Sub-Kategori",
        labels={"Sales": "Sales (USD)", "Sub-Category": "Sub-Kategori"}
    )

    st.plotly_chart(fig)


# MEMBUAT BARIS KEDUA
col1, col2 = st.columns(2)


# BUAT DONUT CHART PROPORSI SEGMEN
with col1:

    segment_sales = (
        filtered.groupby("Segment", as_index=False)["Sales"]
        .sum()
    )

    fig = px.pie(
        segment_sales,
        names="Segment",
        values="Sales",
        title="Proporsi Sales per Segmen",
        hole=0.45
    )

    st.plotly_chart(fig)


# BUAT SCATTER PLOT (SALES VS PROFIT)
with col2:

    fig = px.scatter(
        filtered,
        x="Sales",
        y="Profit",
        color="Category",
        opacity=0.6,
        hover_data=["Sub-Category", "Discount"],
        title="Hubungan Sales dan Profit"
    )

    st.plotly_chart(fig)


# MEMBUAT BARIS KETIGA
col1, col2 = st.columns(2)


# BUAT HISTOGRAM (DISTRIBUSI DISKON)
with col1:

    fig = px.histogram(
        filtered,
        x="Discount",
        nbins=10,
        title="Distribusi Diskon",
        labels={"Discount": "Diskon", "count": "Jumlah Transaksi"}
    )

    st.plotly_chart(fig)


# BUAT HEATMAP (PROFIT PER REGION DAN KATEGORI)
with col2:

    profit_pivot = filtered.pivot_table(
        index="Region",
        columns="Category",
        values="Profit",
        aggfunc="sum"
    )

    fig = px.imshow(
        profit_pivot,
        text_auto=".0f",
        aspect="auto",
        color_continuous_scale="RdYlGn",
        color_continuous_midpoint=0,
        title="Heatmap Profit: Region x Kategori (USD)"
    )

    st.plotly_chart(fig)


# MENGURUTKAN DATA TRANSAKSI
display_df = filtered.sort_values(
    "Order Date",
    ascending=False
)


# MENAMPILKAN DATAFRAME
st.subheader("Data Transaksi")

st.dataframe(
    display_df,
    hide_index=True
)


# MEMBUAT FILE EXCEL DARI HASIL FILTER
output = BytesIO()

with pd.ExcelWriter(output, engine="openpyxl") as writer:
    filtered.to_excel(
        writer,
        index=False,
        sheet_name="Data Filter"
    )

output.seek(0)


# MEMBUAT TOMBOL DOWNLOAD
st.download_button(
    "Download Data Hasil Filter",
    data=output,
    file_name="Data_Transaksi_Filter.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)