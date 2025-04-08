#to run the app: streamlit run streamlit_test2.py

import streamlit as st
import pandas as pd
import plotly.express as px
import matplotlib.pyplot as plt

# Title
st.title("🔋 Energy Consumption Dashboard")
st.write("📊 Visualizing daily **solar power energy** and **consumption** usage")

# Upload CSV
uploaded_file = st.file_uploader("📂 Upload your CSV file", type=["csv"])

if uploaded_file:
    # Load Data
    df = pd.read_csv(uploaded_file)

    # Ensure 'Time' is a DateTime type
    df["Time"] = pd.to_datetime(df["Time"])

    # Show dataset preview
    st.write("📋 **Data Overview**")
    st.dataframe(df.head())

    # Combined Solar Power and Energy Consumption Plot using Plotly
    if "System Pout Consumption Energy [kWh]" in df.columns:
        fig_combined = px.line(df, x="Time", 
                               y=["Solar Power Energy [kWh]", "System Pout Consumption Energy [kWh]"], 
                               title="🌞 Solar Production vs ⚡ Energy Consumption", 
                               labels={"value": "Energy (kWh)", "variable": "Legend"})
        st.plotly_chart(fig_combined)

    # Matplotlib Chart for Solar vs Consumption
    if "System Pout Consumption Energy [kWh]" in df.columns:
        fig, ax = plt.subplots()
        ax.plot(df["Time"], df["Solar Power Energy [kWh]"], label="Solar Power Energy", color='orange')
        ax.plot(df["Time"], df["System Pout Consumption Energy [kWh]"], label="Energy Consumption", color='blue')
        ax.set_title("Solar Production vs Energy Consumption (Matplotlib)")
        ax.set_xlabel("Time")
        ax.set_ylabel("Energy (kWh)")
        ax.legend()
        st.pyplot(fig)

    # Slider to filter high energy days
    min_val = float(df["Solar Power Energy [kWh]"].min())
    max_val = float(df["Solar Power Energy [kWh]"].max())

    threshold = st.slider("⚡ Highlight usage above (kWh):", min_value=min_val, max_value=max_val, value=(min_val + max_val) / 2)

    # Filtered Data
    filtered_data = df[df["Solar Power Energy [kWh]"] > threshold]
    st.write("🔍 **Days with high energy consumption:**")
    st.dataframe(filtered_data)

    # Download filtered data as CSV
    st.download_button(
        label="📥 Download Filtered Data",
        data=filtered_data.to_csv(index=False),
        file_name="filtered_energy_data.csv",
        mime="text/csv",
    )
