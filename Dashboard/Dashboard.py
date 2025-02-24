import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import streamlit as st
import folium
from streamlit_folium import folium_static

def get_highest_avg_station(df):
    highest_avg_station = df.groupby('station')[['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3']].mean().mean(axis=1).idxmax()
    highest_avg_value = df.groupby('station')[['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3']].mean().mean(axis=1).max()
    return highest_avg_station, highest_avg_value

def get_categorical_avg_station(value):
    if value <= 9.0:
        return "Good"
    elif value <= 35.4:
        return "Moderate"
    elif value <= 55.4:
        return "Unhealthy for Sensitive Groups"
    elif value <= 125.4:
        return "Unhealthy"
    elif value <= 225.4:
        return "Very Unhealthy"
    else:
        return "Hazardous"

def get_hourly_value(df):
    hourly_avg = df.groupby(['year', 'month', 'day', 'hour', 'station'])[['PM2.5']].mean().reset_index()
    return hourly_avg
    
all_df = pd.read_csv('Dashboard/all_data_air_quality.csv')
all_df['datetime'] = pd.to_datetime(all_df['datetime'])
all_df['year'] = all_df['datetime'].dt.year
all_df['month'] = all_df['datetime'].dt.month
all_df['day'] = all_df['datetime'].dt.day

with st.sidebar:

    min_date = all_df['datetime'].min()
    max_date = all_df['datetime'].max()

    start_date, end_date = st.date_input(
        label='Rentang Waktu',
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )
    
    start_hour, end_hour = st.slider(
        label='Rentang Jam',
        min_value=0,
        max_value=23,
        value=[0, 23],
        step=1
    )
    
    station_list = all_df['station'].unique().tolist()
    selected_station = st.selectbox('Lokasi', ['Semua'] + station_list)

start_date = pd.to_datetime(start_date)
end_date = pd.to_datetime(end_date)

main_df = all_df[(all_df['datetime'] >= start_date) & (all_df['datetime'] <= end_date)]
main_df = main_df[(main_df['datetime'].dt.hour >= start_hour) & (main_df['datetime'].dt.hour <= end_hour)]

if selected_station != 'Semua':
    main_df = main_df[main_df['station'] == selected_station]

st.header('Dashboard Analisis Kualitas Udara')
st.subheader(f'Data Kualitas Udara (2013 - 2017) - {selected_station} Stasiun')

if selected_station == 'Semua':
    highest_avg_station, highest_avg_value = get_highest_avg_station(all_df)
    air_quality_status = get_categorical_avg_station(highest_avg_value)
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric('Stasiun dengan Rata-rata Indeks Polusi Tertinggi:', value=highest_avg_station)
    with col2:
        st.metric('Nilai Rata-rata Tertinggi:', value=f"{highest_avg_value:.2f}")
    with col3:
        st.metric('Status kualitas udara:', value=air_quality_status)
else:
    if not main_df.empty:
        avg_pollution = main_df[['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3']].mean().mean()
        air_quality_status = get_categorical_avg_station(avg_pollution)
        col1, col2 = st.columns(2)
        with col1:
            st.metric('Nilai Rata-rata Kualitas Udara:', value=f"{avg_pollution:.2f}")
        with col2:
            st.metric('Status kualitas udara:', value=air_quality_status)

if not main_df.empty:
    center_lat = main_df['latitude'].mean()
    center_lon = main_df['longitude'].mean()
    map_air_quality = folium.Map(location=[center_lat, center_lon], zoom_start=10)
    
    stations = main_df[['station', 'latitude', 'longitude']].drop_duplicates()
    for _, row in stations.iterrows():
        folium.Marker(
            [row['latitude'], row['longitude']],
            popup=f"Station {row['station']}",
            icon=folium.Icon(color='blue'),
            tooltip=row['station']
        ).add_to(map_air_quality)
    
    folium_static(map_air_quality)
else:
    st.warning("Tidak ada data untuk rentang waktu dan lokasi yang dipilih.")

st.subheader('Korelasi antar Variable')
if not main_df.empty:
    numeric_cols = ['PM2.5', 'PM10', 'SO2', 'NO2', 'CO', 'O3', 'TEMP', 'PRES', 'DEWP', 'RAIN', 'WSPM']
    corr_matrix = main_df[numeric_cols].corr()
    
    fig, ax = plt.subplots(figsize=(12, 8))
    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', fmt='.2f', linewidths=0.5, ax=ax)
    st.pyplot(fig)
else:
    st.warning("Tidak ada data untuk ditampilkan pada heatmap.")

st.subheader("Analisis Kualitas Udara dalam 24 Jam (Per Stasiun)")
if selected_station != 'Semua':
    hourly_avg_station = get_hourly_value(main_df)
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=hourly_avg_station, x='hour', y='PM2.5', palette='coolwarm', ax=ax)
    ax.set_title(f"Rata-rata PM2.5 dalam 24 Jam - {selected_station} Station")
    ax.set_xlabel("Jam")
    ax.set_ylabel("Konsentrasi Rata-rata PM2.5")
    st.pyplot(fig)
else:
    hourly_avg_station = get_hourly_value(main_df)
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.barplot(data=hourly_avg_station, x='hour', y='PM2.5', palette='coolwarm', ax=ax)
    ax.set_title("Rata-rata Harian PM2.5 (Semua Stasiun)")
    ax.set_xlabel("Jam")
    ax.set_ylabel("Konsentrasi Rata-rata PM2.5")
    st.pyplot(fig)

st.subheader("Analisis Time Series")
if not main_df.empty:
    fig, ax = plt.subplots(figsize=(12, 6))
    sns.lineplot(data=main_df, x='datetime', y='PM2.5', label='PM2.5', ax=ax)
    ax.set_title("Polutan vs Waktu")
    ax.set_xlabel("Waktu")
    ax.set_ylabel("Konsentrasi")
    plt.xticks(rotation=45)
    st.pyplot(fig)
else:
    st.warning("Tidak ada data untuk visualisasi time series.")

st.caption('Dicoding 2025 - Dashboard Analisis Kualitas Udara')
