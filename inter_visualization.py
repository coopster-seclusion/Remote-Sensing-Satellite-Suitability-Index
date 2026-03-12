import pandas as pd
import numpy as np
import plotly.graph_objects as go
from visualization import prepare_plot_data

def plot_suitability_interactive(df, lat, lon, days):
    """
    Generates interactive suitability visualizations for satellite passes using Plotly.
    Primary visualization is a 24-Hour Pass Quality Heatmap with Discrete Mapping.
    """
    plot_df = prepare_plot_data(df)

    # Extract Date and Hour
    plot_df['Date'] = plot_df['Plot Time'].dt.date
    plot_df['Hour'] = plot_df['Plot Time'].dt.hour
    plot_df['Date_str'] = plot_df['Date'].astype(str)

    # Generate a complete grid for Date x Hour (0-23)
    min_date = plot_df['Date'].min()
    # Force the display to exactly `days` (typically 14)
    all_dates = pd.date_range(start=min_date, periods=days).date
    
    date_strs = [str(d) for d in all_dates]
    hours = list(range(24))
    
    z_quality = np.full((len(date_strs), 24), np.nan)
    text_labels = np.full((len(date_strs), 24), "", dtype=object)
    custom_data = np.empty((len(date_strs), 24, 5), dtype=object)
    
    # Pre-fill N/A for empty gaps
    for i in range(len(date_strs)):
        for j in range(24):
            custom_data[i, j, 0] = "N/A"
            custom_data[i, j, 1] = "N/A"
            custom_data[i, j, 2] = "N/A"
            custom_data[i, j, 3] = "N/A"
            custom_data[i, j, 4] = "N/A"

    # Discrete Mapping - no averaging, exactly mapped
    annotations = []
    for _, row in plot_df.iterrows():
        d_str = row['Date_str']
        h = int(row['Hour'])
        if d_str in date_strs:
            d_idx = date_strs.index(d_str)
            h_idx = h
            
            z_quality[d_idx, h_idx] = row['Quality Score']
            text_labels[d_idx, h_idx] = str(row['Pass_Index'])
            custom_data[d_idx, h_idx, 0] = str(row['Pass_Index'])
            custom_data[d_idx, h_idx, 1] = row['Pass Start (UTC ISO-8601)']
            custom_data[d_idx, h_idx, 2] = row['Pass End (UTC ISO-8601)']
            custom_data[d_idx, h_idx, 3] = f"{row['Quality Score']:.3f}"
            custom_data[d_idx, h_idx, 4] = row['Rise Time (Local)']

            font_color = "black" if 0.55 <= row['Quality Score'] <= 1.0 else "white"
            annotations.append(
                go.layout.Annotation(
                    x=h_idx,
                    y=d_str,
                    text=str(row['Pass_Index']),
                    showarrow=False,
                    font=dict(color=font_color, size=12)
                )
            )

    custom_colorscale = [
        [0.0, 'darkblue'],
        [0.5, 'yellow'],
        [1.0, 'orange']
    ]

    heatmap = go.Heatmap(
        z=z_quality,
        x=hours,
        y=date_strs,
        colorscale=custom_colorscale,
        colorbar=dict(title='Pass Quality'),
        zmin=0.2, zmax=1,
        hoverongaps=False,
        hovertemplate='<b>Date:</b> %{y}<br><b>Rise Time (Local):</b> %{customdata[4]}<br><b>Pass Index:</b> %{customdata[0]}<br><b>Start:</b> %{customdata[1]}<br><b>End:</b> %{customdata[2]}<br><b>Quality Score:</b> %{customdata[3]}<extra></extra>',
        customdata=custom_data
    )

    fig = go.Figure(data=heatmap)

    # Calculate an optimal height so aspect ratio remains legible (min 400px)
    plot_height = max(400, len(date_strs) * 30 + 150)

    fig.update_layout(
        title=f'FireSat-0 14-Day High-Precision Heatmap (Lat: {lat}, Lon: {lon})',
        xaxis=dict(
            title='Hour of Day (Local Time)',
            tickmode='linear',
            tick0=0,
            dtick=1,
            range=[-0.5, 23.5],
            gridcolor='#333333'
        ),
        yaxis=dict(
            title='Date',
            autorange='reversed',  # Earliest dates at the top
            gridcolor='#333333'
        ),
        plot_bgcolor='#1E1E1E',  # Dark neutral background color for null
        paper_bgcolor='#121212',
        font=dict(color='white'),
        height=plot_height,
        margin=dict(l=80, r=80, t=80, b=80),
        clickmode='event+select',
        annotations=annotations
    )

    return fig
