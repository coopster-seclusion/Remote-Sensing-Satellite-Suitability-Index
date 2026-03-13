import streamlit as st
import pandas as pd
import re
import pytz
from visualization import plot_suitability
from calculations import fetch_satellite_data, calculate_passes

st.set_page_config(page_title="FireSat Pass Predictor", page_icon="🛰️", layout="centered")

@st.cache_resource(ttl=3600)
def get_satellite_data():
    """Fetch the latest TLE data from Celestrak for FIRESAT 0."""
    return fetch_satellite_data()

st.title("🛰️ FireSat Imaging Windows")
st.markdown("""
This beta app predicts overhead passes for the **FIRESAT 0 (MUSAT-4)** satellite (NORAD ID: 63256) 
over a specified geographic location. 

### Sensing Parameters
FireSat has a **1,500 km swath width** operating from a **~587 km altitude (SSO)**. 
Because of this wide field of view, an "observable pass" for a specific ground target occurs anytime the satellite reaches a minimum elevation of **~33.4°** above the horizon. Passes below this elevation mean the target is outside the 1,500km observing swath.

The outputs use standard datetime formats ready for geospatial analysis (e.g., GeoPandas).
""")

# Input section
st.header("Search Parameters", divider="blue")
col1, col2 = st.columns(2)
with col1:
    lat_input = st.text_input("Latitude (Decimal Degrees)", value="34.0522", help="Positive for North, negative for South.")
with col2:
    lon_input = st.text_input("Longitude (Decimal Degrees)", value="-118.2437", help="Positive for East, negative for West.")

days = 14
col3, col4 = st.columns(2)
with col3:
    st.info("Forecast Range is locked to 14 Days.")
with col4:
    local_tz_str = st.selectbox("Local Timezone", options=pytz.common_timezones, index=pytz.common_timezones.index('America/Los_Angeles'))

col5, col6 = st.columns([1, 1])
with col5:
    predict_standard = st.button("Predict Passes", type="primary")
with col6:
    predict_interactive = st.button("Predict Pass - Interactive", type="primary")

if predict_standard or predict_interactive:
    lat_valid = bool(re.match(r"^[-+]?([1-8]?\d(\.\d+)?|90(\.0+)?)$", lat_input))
    lon_valid = bool(re.match(r"^[-+]?((1[0-7]\d|[1-9]?\d)(\.\d+)?|180(\.0+)?)$", lon_input))

    if not lat_valid or not lon_valid:
        st.error("Invalid Latitude or Longitude coordinate format.")
    else:
        lat = float(lat_input)
        lon = float(lon_input)
        with st.spinner("Fetching orbital data and calculating passes..."):
            sat = get_satellite_data()
        if not sat:
            st.error("Could not fetch satellite data from Celestrak. Please try again later.")
        else:
            local_tz = pytz.timezone(local_tz_str)
            passes = calculate_passes(sat, lat, lon, days)
            
            if not passes:
                st.warning(f"No passes found over this location in the next {days} days.")
            else:
                st.success(f"Found {len(passes)} passes in the next {days} days!")
                
                # Format into a dataframe
                pass_data = []
                for p in passes:
                    try:
                        # Extract UTC datetimes
                        rise_utc = p['rise_time'].utc_datetime()
                        culminate_utc = p['culminate_time'].utc_datetime()
                        set_utc = p['set_time'].utc_datetime()
                        
                        # Apply local timezone
                        rise_local = rise_utc.astimezone(local_tz)
                        
                        # Add to list
                        pass_data.append({
                            "Setup/Pass Index": len(pass_data) + 1,
                            "Rise Time (Local)": rise_local.strftime('%Y-%m-%d %H:%M:%S %Z'),
                            "Max Elevation (deg)": round(p['max_elevation'], 1),
                            "Duration (sec)": round(p['duration_seconds']),
                            "Quality Score": p['suitability_index'],
                            "Pass Start (UTC ISO-8601)": rise_utc.strftime('%Y-%m-%dT%H:%M:%SZ'),
                            "Pass Peak (UTC ISO-8601)": culminate_utc.strftime('%Y-%m-%dT%H:%M:%SZ'),
                            "Pass End (UTC ISO-8601)": set_utc.strftime('%Y-%m-%dT%H:%M:%SZ')
                        })
                    except KeyError:
                        # Skip incomplete passes (e.g., if observation starts right in the middle of a pass)
                        continue
                
                df = pd.DataFrame(pass_data)

                df.set_index("Setup/Pass Index", inplace=True)
                
                st.dataframe(df, use_container_width=True)
                
                # Download CSV
                csv = df.to_csv().encode('utf-8')
                st.download_button(
                    label="Download data as CSV",
                    data=csv,
                    file_name=f'firesat_passes_{lat}_{lon}.csv',
                    mime='text/csv',
                )

                st.header("Pass Suitability Analysis", divider="blue")
                
                # Generate plot from the separate visualization module
                if predict_interactive:
                    from inter_visualization import plot_suitability_interactive
                    fig = plot_suitability_interactive(df, lat, lon, days)
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    fig = plot_suitability(df, lat, lon, days)
                    st.pyplot(fig)
