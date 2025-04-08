import streamlit as st
import pandas as pd
import plotly.express as px

# Load data
data = {'Time': ['2024-03-01', '2024-03-02', '2024-03-03'],
        'Energy (kWh)': [120, 150, 170]}
#df = pd.DataFrame(data)

df_sys= pd.read_csv("day_kWh.csv")
df_solar=df_sys["Solar Power Energy [kWh]"]
df=df_sys

print("-------------------------")

print(df.columns)
print("-------------------------")

# Streamlit UI
st.title("🔋 Energy Consumption Dashboard")
st.write("📊 Visualizing energy usage over time")

#fig = px.line(df, x="Time", y="Energy (kWh)", title="Daily Energy Consumption")
fig = px.line(df, x="Time", y="Solar Power Energy [kWh]", title="Daily Energy Consumption")

st.plotly_chart(fig)

# Add a slider to filter energy values
threshold = st.slider("Highlight usage above (kWh):", min_value=0, max_value=100, value=50)
#filtered_data = df[df["Energy (kWh)"] > threshold]

filtered_data = df[df["Solar Power Energy [kWh]"] > threshold]
st.write("🔍 Days with high energy consumption:", filtered_data)
