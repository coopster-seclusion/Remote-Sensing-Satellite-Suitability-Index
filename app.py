import streamlit as st
import pandas as pd
from skyfield.api import wgs84, load, EarthSatellite
import pytz
from datetime import timedelta

st.set_page_config(page_title="FireSat Pass Predictor", page_icon="🛰️", layout="centered")

@st.cache_resource(ttl=3600)
def get_satellite_data():
    """Fetch the latest TLE data from Celestrak for FIRESAT 0."""
    stations_url = 'https://celestrak.org/NORAD/elements/gp.php?CATNR=63256'
    satellites = load.tle_file(stations_url)
    if satellites:
        return satellites[0]
    return None

def calculate_passes(satellite, lat, lon, days):
    """
    Calculate imaging passes. 
    A 1500km swath from a 587km orbit translates to roughly a 33.4 degree minimum elevation angle
    from the observer's perspective to be within the observable ground swath.
    """
    min_elevation = 33.4  # Minimum viable elevation for the 1500km FireSat swath at 587km altitude
    
    ts = load.timescale()
    t0 = ts.now()
    t1 = ts.utc(t0.utc_datetime() + timedelta(days=days))
    
    # Define the observer location
    observer = wgs84.latlon(lat, lon)
    
    # Calculate passes
    t, events = satellite.find_events(observer, t0, t1, altitude_degrees=min_elevation)
    
    passes = []
    current_pass = {}
    
    for ti, event in zip(t, events):
        if event == 0:  # Rise
            current_pass['rise_time'] = ti
        elif event == 1:  # Culminate
            current_pass['culminate_time'] = ti
            # Calculate elevation
            difference = satellite - observer
            topocentric = difference.at(ti)
            alt, az, distance = topocentric.altaz()
            current_pass['max_elevation'] = alt.degrees
        elif event == 2:  # Set
            current_pass['set_time'] = ti
            if 'rise_time' in current_pass:
                # Calculate duration in seconds
                duration_seconds = (current_pass['set_time'] - current_pass['rise_time']) * 24 * 60 * 60
                
                # Only save passes that actually cross the 33.4 degree threshold 
                # (find_events sometimes flags an event if max elevation barely clips it or fails)
                if current_pass.get('max_elevation', 0) >= 33.4:
                    current_pass['duration_seconds'] = duration_seconds
                    passes.append(current_pass)
            current_pass = {}
            
    return passes

st.title("🛰️ FireSat (Muon Space) Imaging Windows")
st.markdown("""
This app predicts overhead passes for the **FIRESAT 0 (MUSAT-4)** satellite (NORAD ID: 63256) 
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
    lat = st.number_input("Latitude (Decimal Degrees)", value=34.0522, format="%.4f", help="Positive for North, negative for South.")
with col2:
    lon = st.number_input("Longitude (Decimal Degrees)", value=-118.2437, format="%.4f", help="Positive for East, negative for West.")

col3, col4 = st.columns(2)
with col3:
    days = st.slider("Forecast Range (Days)", min_value=1, max_value=14, value=3)
with col4:
    local_tz_str = st.selectbox("Local Timezone", options=pytz.common_timezones, index=pytz.common_timezones.index('America/Los_Angeles'))

if st.button("Predict Passes", type="primary"):
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
