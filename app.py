import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests

# Download the merged CSV from Google Drive
url = "https://drive.google.com/uc?export=download&id=1B4dl6l3UeZHY_DJzRmHe0u43yezRv939"
response = requests.get(url)
with open("FCT_Analyzed.csv", "wb") as f:
    f.write(response.content)

# Load data from CSV
df = pd.read_csv("FCT_Analyzed_Merged.csv")

# Title
st.title("FCT Election Integrity Dashboard (2023)")

# Sidebar for filters
st.sidebar.header("Filters")
selected_lga = st.sidebar.multiselect("Select Area Council (LGA)", options=df['LGA'].unique(), default=df['LGA'].unique())
selected_ward = st.sidebar.multiselect("Select Ward", options=df['Ward'].unique(), default=df['Ward'].unique())
selected_party = st.sidebar.selectbox("Select Party for Analysis", options=['APC', 'LP', 'PDP', 'NNPP'], index=0)

# Filter the DataFrame based on selections
filtered_df = df[df['LGA'].isin(selected_lga) & df['Ward'].isin(selected_ward)]

# Section 1: Live Vote Counts
st.subheader("Live Vote Counts (Total Votes per Party)")
party_votes = {
    'APC': filtered_df['APC'].sum() if 'APC' in filtered_df.columns else 0,
    'LP': filtered_df['LP'].sum() if 'LP' in filtered_df.columns else 0,
    'PDP': filtered_df['PDP'].sum() if 'PDP' in filtered_df.columns else 0,
    'NNPP': filtered_df['NNPP'].sum() if 'NNPP' in filtered_df.columns else 0
}
vote_counts_df = pd.DataFrame(list(party_votes.items()), columns=['Party', 'Total Votes'])
fig1 = px.bar(vote_counts_df, x='Party', y='Total Votes', title="Total Votes per Party")
st.plotly_chart(fig1)

# Section 2: Percentage Breakdown by Region
st.subheader("Vote Share by Area Council (All Parties)")
party_percentages = filtered_df.groupby('LGA')[['APC_Percentage', 'LP_Percentage', 'PDP_Percentage', 'NNPP_Percentage']].mean().reset_index()
fig2 = px.bar(party_percentages, x='LGA', y=['APC_Percentage', 'LP_Percentage', 'PDP_Percentage', 'NNPP_Percentage'],
              barmode='stack', title="Vote Share by Area Council")
st.plotly_chart(fig2)

# Section 3: Turnout Statistics (Raw Numbers)
st.subheader("Turnout Statistics (Registered vs. Accredited Voters)")
if 'Registered_Voters' in filtered_df.columns and 'Accredited_Voters' in filtered_df.columns:
    total_registered = filtered_df['Registered_Voters'].sum()
    total_accredited = filtered_df['Accredited_Voters'].sum()
    turnout_data = pd.DataFrame({
        'Category': ['Registered Voters', 'Accredited Voters'],
        'Count': [total_registered, total_accredited]
    })
    fig3 = px.bar(turnout_data, x='Category', y='Count', title="Registered vs. Accredited Voters")
    st.plotly_chart(fig3)
else:
    st.write("Registered_Voters or Accredited_Voters data not available.")

# Section 4: Turnout by Area Council and Ward
st.subheader("Turnout Percentage by Area Council and Ward")
turnout_by_lga = filtered_df.groupby('LGA')['Turnout_Percentage'].mean().reset_index()
fig4 = px.bar(turnout_by_lga, x='LGA', y='Turnout_Percentage', title="Turnout Percentage by Area Council")
st.plotly_chart(fig4)

if len(selected_lga) > 0:
    turnout_by_ward = filtered_df.groupby(['LGA', 'Ward'])['Turnout_Percentage'].mean().reset_index()
    fig5 = px.bar(turnout_by_ward, x='Ward', y='Turnout_Percentage', color='LGA', title="Turnout Percentage by Ward")
    st.plotly_chart(fig5)

# Section 5: Geographical Mapping (Votes by Polling Unit)
st.subheader("Geographical Mapping (Votes by Polling Unit)")
if 'latitude_y' in filtered_df.columns and 'longitude_y' in filtered_df.columns:
    # Calculate total votes per polling unit
    filtered_df['Total_Votes'] = filtered_df[['APC', 'LP', 'PDP', 'NNPP']].sum(axis=1)
    cluster_radius = st.selectbox("Select Clustering Radius", options=['500m', '1km', '2km'], index=0)
    cluster_col = f'Cluster_{cluster_radius}'
    if cluster_col in filtered_df.columns:
        fig6 = px.scatter_mapbox(filtered_df, lat='latitude_y', lon='longitude_y', size='Total_Votes',
                                 color=cluster_col, hover_name='PU.Name',
                                 hover_data=['Total_Votes', f'{selected_party}_Percentage'],
                                 mapbox_style="open-street-map", zoom=10)
        st.plotly_chart(fig6)
    else:
        st.write(f"Clustering data for {cluster_radius} not available.")
else:
    st.write("Latitude or longitude columns not available for mapping.")

# Section 6: Geographical Mapping (Anomaly Detection)
st.subheader("Geographical Mapping (Anomaly Detection)")
if 'latitude_y' in filtered_df.columns and 'longitude_y' in filtered_df.columns and 'Anomaly_Label_y' in filtered_df.columns:
    fig7 = px.scatter_mapbox(filtered_df, lat='latitude_y', lon='longitude_y', color='Anomaly_Label_y',
                             hover_name='PU.Name', hover_data=['Anomaly_Label_y'],
                             mapbox_style="open-street-map", zoom=10)
    st.plotly_chart(fig7)
else:
    st.write("Latitude, longitude, or Anomaly_Label_y columns not available for mapping.")

# Section 7: Historical Comparisons
st.subheader("Historical Comparisons (2019 vs. 2023)")
# Turnout Comparison
election_summary = pd.DataFrame({
    'Year': [2019, 2023],
    'Turnout_Percentage': [35.66, (filtered_df['Accredited_Voters'].sum() / filtered_df['Registered_Voters'].sum()) * 100]
})
fig8 = px.bar(election_summary, x='Year', y='Turnout_Percentage', title="Turnout Percentage: 2019 (National) vs. 2023 (FCT)")
st.plotly_chart(fig8)

# Party Vote Share Comparison (using placeholder 2019 national data)
historical_vote_share = pd.DataFrame({
    'Year': [2019, 2019, 2019, 2019, 2023, 2023, 2023, 2023],
    'Party': ['APC', 'LP', 'PDP', 'NNPP', 'APC', 'LP', 'PDP', 'NNPP'],
    'Vote_Share': [
        55.6, 5.0, 35.0, 4.4,  # 2019 national averages (placeholder)
        filtered_df['APC_Percentage'].mean(),
        filtered_df['LP_Percentage'].mean(),
        filtered_df['PDP_Percentage'].mean(),
        filtered_df['NNPP_Percentage'].mean()
    ]
})
fig9 = px.bar(historical_vote_share, x='Party', y='Vote_Share', color='Year', barmode='group',
              title="Party Vote Share: 2019 (National) vs. 2023 (FCT)")
st.plotly_chart(fig9)

# Section 8: Anomaly Distribution
st.subheader("Anomaly Distribution by Area Council")
if 'Anomaly_Label_y' in filtered_df.columns:
    anomaly_by_lga = filtered_df.groupby('LGA')['Anomaly_Label_y'].value_counts().unstack().fillna(0)
    fig10 = px.bar(anomaly_by_lga, barmode='stack', title="Anomaly Distribution by Area Council")
    st.plotly_chart(fig10)
else:
    st.write("Anomaly_Label_y column not available for anomaly distribution.")