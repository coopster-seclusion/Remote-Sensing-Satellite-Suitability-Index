import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

def plot_suitability(df, lat, lon, days):
    """
    Generates suitability visualizations for satellite passes.
    """
    # We need `Rise Time (Local)` as datetime objects for matplotlib
    plot_df = df.copy()
    plot_df['Pass_Index'] = plot_df.index
    
    # Parse the datetime. The string format is '%Y-%m-%d %H:%M:%S %Z'
    # Extract just the datetime part, discarding the timezone abbreviation
    plot_df['Plot Time'] = pd.to_datetime(plot_df['Rise Time (Local)'].apply(lambda x: " ".join(x.split()[:2])))

    plt.style.use('ggplot')
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))

    # Plot 1: Timeline of Imaging Windows
    ax1.scatter(plot_df['Plot Time'], [1]*len(plot_df), 
                s=plot_df['Quality Score']*1000, 
                c=plot_df['Quality Score'], cmap='YlOrRd', 
                alpha=0.8, edgecolors='k')

    # Label passes on timeline scatter plot
    for _, row in plot_df.iterrows():
        text_color = 'white' if row['Quality Score'] >= 0.6 else 'black'
        ax1.text(row['Plot Time'], 1, 
                 str(row['Pass_Index']), 
                 color=text_color, fontsize=10, fontweight='bold',
                 ha='center', va='center')

    ax1.set_yticks([])
    ax1.set_title(f'FireSat-0 Imaging Windows: Next {days} Days (Lat: {lat}, Lon: {lon})', fontsize=14)
    ax1.set_xlabel('Date and Time (Local)')
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%d %b\n%H:%M'))

    # Annotate the best window
    best_pass = plot_df.loc[plot_df['Quality Score'].idxmax()]
    best_time_str = best_pass['Plot Time'].strftime('%Y-%m-%d %H:%M:%S')
    
    # Calculate position ratio to dynamically align text so it doesn't clip
    timeline_min = plot_df['Plot Time'].min()
    timeline_max = plot_df['Plot Time'].max()
    timeline_dur = (timeline_max - timeline_min).total_seconds()
    
    if timeline_dur > 0:
        pos_ratio = (best_pass['Plot Time'] - timeline_min).total_seconds() / timeline_dur
    else:
        pos_ratio = 0.5
        
    if pos_ratio < 0.2:
        # Near left edge: anchor text to grow to the right
        ha = 'left'
    elif pos_ratio > 0.8:
        # Near right edge: anchor text to grow to the left
        ha = 'right'
    else:
        # Center normally
        ha = 'center'

    ax1.annotate(f"BEST WINDOW (Pass {best_pass['Pass_Index']})\nDate/Time: {best_time_str}\nElev: {best_pass['Max Elevation (deg)']}°\nDur: {best_pass['Duration (sec)']}s", 
                 xy=(best_pass['Plot Time'], 1), 
                 xytext=(0, 50), textcoords='offset points',
                 ha=ha, va='bottom',
                 bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="black", alpha=0.9),
                 arrowprops=dict(arrowstyle='->', color='black', shrinkB=15))

    # Plot 2: Quality Analysis (Duration vs Elevation)
    sc = ax2.scatter(plot_df['Max Elevation (deg)'], plot_df['Duration (sec)'], 
                    c=plot_df['Quality Score'], cmap='YlOrRd', s=200, edgecolors='k')
    fig.colorbar(sc, ax=ax2, label='Suitability Score')
    ax2.set_xlabel('Max Elevation (Degrees)')
    ax2.set_ylabel('Duration (Seconds)')
    ax2.set_title('Pass Quality Comparison', fontsize=12)

    # Label passes on scatter plot
    for _, row in plot_df.iterrows():
        # High quality score means darker red circles -> use white text 
        # Low quality score means lighter yellow/orange circles -> use black text
        # Threshold of 0.6 works well for the YlOrRd colormap transition
        text_color = 'white' if row['Quality Score'] >= 0.6 else 'black'
        
        ax2.text(row['Max Elevation (deg)'], row['Duration (sec)'], 
                 str(row['Pass_Index']), 
                 color=text_color, fontsize=10, fontweight='bold',
                 ha='center', va='center')

    plt.tight_layout()
    return fig
