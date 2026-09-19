# dashboard/risk_heatmap.py
"""
Executive Dynamic Risk Heatmap.
Visualizes the real-time Dynamic Risk Index (DRI) across the pipeline network 
using interactive geospatial mapping.
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(page_title="PLRM Executive Risk Heatmap", layout="wide", page_icon="️")

st.title("🗺️ Executive Dynamic Risk Heatmap")
st.markdown("Real-time Risk-Based Inspection (RBI) & Consequence Analysis | Powered by **Nebius AI Cloud**")

# ==============================================================================
# 1. Mock Data Generation (In production, fetch from Nebius Cloud API)
# ==============================================================================
@st.cache_data(ttl=60) # Cache for 60 seconds to prevent API spamming
def load_pipeline_data():
    # Simulating a pipeline route from the Permian Basin (Midland, TX) to a refinery (Houston, TX)
    np.random.seed(42)
    num_nodes = 25
    
    # Generate linear coordinates for the pipeline route
    lats = np.linspace(31.99, 29.76, num_nodes)
    lons = np.linspace(-102.07, -95.36, num_nodes)
    
    # Simulate Risk Metrics
    data = []
    for i in range(num_nodes):
        # Inject a "Critical" cluster around node 15 (simulating a high-risk zone)
        if 14 <= i <= 17:
            pof = np.random.uniform(70, 95)
            cof = np.random.uniform(80, 100)
        elif i in [5, 20]:
            pof = np.random.uniform(40, 60) # High risk
            cof = np.random.uniform(40, 60)
        else:
            pof = np.random.uniform(5, 25) # Normal
            cof = np.random.uniform(10, 40)
            
        dri = (pof * cof) / 100.0
        
        if dri >= 75: tier = "CRITICAL"
        elif dri >= 50: tier = "HIGH"
        elif dri >= 25: tier = "MEDIUM"
        else: tier = "LOW"
        
        data.append({
            "node_id": f"NODE-{100+i}",
            "lat": lats[i] + np.random.normal(0, 0.05),
            "lon": lons[i] + np.random.normal(0, 0.05),
            "pof": round(pof, 1),
            "cof": round(cof, 1),
            "dri": round(dri, 1),
            "risk_tier": tier,
            "corrosion_rate": round(np.random.uniform(0, 1), 2),
            "physics_residual": round(np.random.uniform(0, 1), 2),
            "mitigation": f"Tier {tier} protocol active. See full dossier."
        })
    return pd.DataFrame(data)

df = load_pipeline_data()

# ==============================================================================
# 2. Sidebar: Executive Filters & Summary Metrics
# ==============================================================================
st.sidebar.header("📊 Network Summary")
total_nodes = len(df)
critical_nodes = len(df[df['risk_tier'] == 'CRITICAL'])
high_nodes = len(df[df['risk_tier'] == 'HIGH'])
avg_dri = df['dri'].mean()

st.sidebar.metric("Total Pipeline Nodes", total_nodes)
st.sidebar.metric("Critical Risk Nodes", critical_nodes, delta="⚠️ Immediate Action" if critical_nodes > 0 else "✅ Secure")
st.sidebar.metric("High Risk Nodes", high_nodes)
st.sidebar.metric("Network Avg. DRI", f"{avg_dri:.1f}")

st.sidebar.divider()
st.sidebar.subheader("🔍 Filter by Risk Tier")
selected_tiers = st.sidebar.multiselect(
    "Select Tiers to Display:",
    options=["CRITICAL", "HIGH", "MEDIUM", "LOW"],
    default=["CRITICAL", "HIGH", "MEDIUM", "LOW"]
)

filtered_df = df[df['risk_tier'].isin(selected_tiers)]

# ==============================================================================
# 3. Main Layout: The Interactive Heatmap
# ==============================================================================
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("Geospatial Risk Distribution")
    
    # Define the custom colorscale for the heatmap (Green -> Yellow -> Orange -> Red)
    colorscale = [
        [0.0, 'rgb(0, 200, 83)'],    # Low (Green)
        [0.33, 'rgb(255, 235, 59)'], # Medium (Yellow)
        [0.66, 'rgb(255, 152, 0)'],  # High (Orange)
        [1.0, 'rgb(244, 67, 54)']    # Critical (Red)
    ]

    fig = go.Figure()

    # Trace 1: The Pipeline Route (Background Line)
    fig.add_trace(go.Scattergeo(
        lon=df['lon'],
        lat=df['lat'],
        mode='lines',
        line=dict(width=2, color='rgba(100, 100, 100, 0.5)'),
        hoverinfo='skip',
        showlegend=False,
        name='Pipeline Route'
    ))

    # Trace 2: The Risk Nodes (Interactive Markers)
    fig.add_trace(go.Scattergeo(
        lon=filtered_df['lon'],
        lat=filtered_df['lat'],
        mode='markers+text',
        text=filtered_df['node_id'],
        textposition="top center",
        textfont=dict(size=8, color='white'),
        marker=dict(
            size=filtered_df['dri'] / 2 + 5, # Scale marker size by DRI
            color=filtered_df['dri'],
            colorscale=colorscale,
            cmin=0,
            cmax=100,
            line=dict(width=1, color='white'),
            opacity=0.9,
            colorbar=dict(
                title="Dynamic Risk Index (DRI)",
                x=1.02,
                thickness=15
            )
        ),
        hovertemplate=(
            "<b>%{text}</b><br>"
            "Risk Tier: %{customdata[0]}<br>"
            "DRI: %{customdata[1]}<br>"
            "PoF: %{customdata[2]}%<br>"
            "CoF: %{customdata[3]}%<br>"
            "<extra></extra>"
        ),
        customdata=filtered_df[['risk_tier', 'dri', 'pof', 'cof']],
        name='Sensor Nodes'
    ))

    # Layout Configuration (Dark "Control Room" Theme)
    fig.update_layout(
        geo=dict(
            scope='usa',
            projection=dict(type='albers usa'), # Excellent for US pipeline maps
            showland=True,
            landcolor='rgb(30, 30, 30)',
            showocean=True,
            oceancolor='rgb(10, 10, 20)',
            showlakes=True,
            lakecolor='rgb(15, 15, 25)',
            showrivers=True,
            rivercolor='rgb(20, 20, 30)'
        ),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        font=dict(color='white'),
        height=650,
        margin=dict(l=0, r=0, t=30, b=0),
        hovermode='closest'
    )

    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("️ Active Mitigation Plans")
    st.markdown("Top 5 highest risk nodes requiring immediate attention.")
    
    # Sort by DRI descending and take top 5
    top_risks = filtered_df.nlargest(5, 'dri')
    
    if top_risks.empty:
        st.info("No active high-risk nodes in the selected filters.")
    else:
        for index, row in top_risks.iterrows():
            color = "🔴" if row['risk_tier'] == 'CRITICAL' else "🟠" if row['risk_tier'] == 'HIGH' else "🟡"
            with st.expander(f"{color} {row['node_id']} (DRI: {row['dri']})"):
                st.markdown(f"**Risk Tier:** {row['risk_tier']}")
                st.markdown(f"**PoF:** {row['pof']}% | **CoF:** {row['cof']}%")
                st.markdown(f"**Primary Drivers:**")
                st.markdown(f"- Corrosion Index: {row['corrosion_rate']}")
                st.markdown(f"- Physics Residual: {row['physics_residual']}")
                st.divider()
                st.markdown(f"**AI Mitigation Plan:**")
                st.caption(row['mitigation'])

# ==============================================================================
# 4. Bottom Section: Detailed Data Table
# ==============================================================================
st.divider()
st.subheader("📋 Comprehensive Node Risk Registry")
st.dataframe(
    filtered_df.sort_values(by='dri', ascending=False),
    use_container_width=True,
    hide_index=True,
    column_config={
        "node_id": st.column_config.TextColumn("Node ID"),
        "risk_tier": st.column_config.TextColumn("Risk Tier"),
        "dri": st.column_config.ProgressColumn("DRI (0-100)", min_value=0, max_value=100, format="%f"),
        "pof": st.column_config.NumberColumn("PoF (%)", format="%.1f"),
        "cof": st.column_config.NumberColumn("CoF (%)", format="%.1f")
    }
)
