import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np

# Page configuration for mobile-friendly view
st.set_page_config(
    page_title="Industry Real Estate Showcase Dashboard",
    page_icon="🏢",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load data
@st.cache_data
def load_data():
    df = pd.read_csv('enriched_properties.csv')
    
    # Clean transaction price column
    if 'Transaction Price  ' in df.columns:
        df['Price'] = df['Transaction Price  '].astype(str).str.replace('RM', '').str.replace(',', '').str.strip()
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
    elif 'Transaction Price' in df.columns:
        df['Price'] = df['Transaction Price'].astype(str).str.replace('RM', '').str.replace(',', '').str.strip()
        df['Price'] = pd.to_numeric(df['Price'], errors='coerce')
        
    return df

df = load_data()

# App Title & Header
st.title("🏢 Industry Real Estate Analytics Dashboard")
st.caption("Interactive Showcase | Scan QR to explore market insights")

# Sidebar Filters
st.sidebar.header("🔍 Filter Properties")

districts = st.sidebar.multiselect("Select District(s)", options=sorted(df['District'].dropna().unique()), default=[])
prop_types = st.sidebar.multiselect("Select Property Type(s)", options=sorted(df['Property Type'].dropna().unique()), default=[])
tenure = st.sidebar.multiselect("Select Tenure", options=sorted(df['Tenure'].dropna().unique()), default=[])

# Apply filters
filtered_df = df.copy()
if districts:
    filtered_df = filtered_df[filtered_df['District'].isin(districts)]
if prop_types:
    filtered_df = filtered_df[filtered_df['Property Type'].isin(prop_types)]
if tenure:
    filtered_df = filtered_df[filtered_df['Tenure'].isin(tenure)]

# KPI Row
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Transactions", f"{len(filtered_df):,}")
with col2:
    median_price = filtered_df['Price'].median() if 'Price' in filtered_df and len(filtered_df) > 0 else 0
    st.metric("Median Price", f"RM {median_price:,.0f}" if pd.notnull(median_price) else "N/A")
with col3:
    avg_cbd = filtered_df['dist_to_kl_cbd_km'].mean() if 'dist_to_kl_cbd_km' in filtered_df and len(filtered_df) > 0 else 0
    st.metric("Avg Dist to KL CBD", f"{avg_cbd:.1f} km")
with col4:
    avg_station = filtered_df['dist_to_nearest_station_km'].mean() if 'dist_to_nearest_station_km' in filtered_df and len(filtered_df) > 0 else 0
    st.metric("Avg Dist to Rail Station", f"{avg_station:.1f} km")

st.markdown("---")

# Tab Layout for Clean Navigation on Mobile
tab1, tab2, tab3 = st.tabs(["🗺️ Interactive Map", "📊 Market Insights", "🚆 Connectivity & Proximity"])

with tab1:
    st.subheader("Property Distribution & Pricing Map")
    map_df = filtered_df.dropna(subset=['latitude', 'longitude', 'Price']).head(2000) # Limit points for performance
    
    if len(map_df) > 0:
        fig_map = px.scatter_mapbox(
            map_df,
            lat="latitude",
            lon="longitude",
            color="Price",
            size="dist_to_nearest_station_km",
            hover_name="Scheme Name/Area",
            hover_data=["Property Type", "District", "Price"],
            color_continuous_scale=px.colors.cyclical.IceFire,
            zoom=9,
            height=500
        )
        fig_map.update_layout(mapbox_style="open-street-map", margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("No geospatial data available for current selection.")

with tab2:
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("Top Districts by Volume")
        dist_counts = filtered_df['District'].value_counts().reset_index().head(10)
        dist_counts.columns = ['District', 'Count']
        fig_bar = px.bar(dist_counts, x='Count', y='District', orientation='h', color='Count', color_continuous_scale='Blues')
        fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
        st.plotly_chart(fig_bar, use_container_width=True)
        
    with col_b:
        st.subheader("Price Distribution by Property Type")
        fig_box = px.box(filtered_df.dropna(subset=['Price']), x='Property Type', y='Price', color='Property Type')
        fig_box.update_layout(showlegend=False, xaxis_tickangle=-45)
        st.plotly_chart(fig_box, use_container_width=True)

with tab3:
    st.subheader("Connectivity vs. Price Dynamics")
    col_c, col_d = st.columns(2)
    
    with col_c:
        fig_scat1 = px.scatter(
            filtered_df.dropna(subset=['dist_to_kl_cbd_km', 'Price']), 
            x="dist_to_kl_cbd_km", 
            y="Price", 
            color="Tenure",
            trendline="lowess",
            title="Distance to KL CBD vs. Price"
        )
        st.plotly_chart(fig_scat1, use_container_width=True)
        
    with col_d:
        fig_scat2 = px.scatter(
            filtered_df.dropna(subset=['dist_to_nearest_station_km', 'Price']), 
            x="dist_to_nearest_station_km", 
            y="Price", 
            color="District",
            title="Distance to Nearest Station vs. Price"
        )
        st.plotly_chart(fig_scat2, use_container_width=True)

st.markdown("---")
st.dataframe(filtered_df[['Property Type', 'District', 'Scheme Name/Area', 'Tenure', 'Price', 'dist_to_kl_cbd_km']].head(50), use_container_width=True)
