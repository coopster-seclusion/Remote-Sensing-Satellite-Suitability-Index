import numpy as np
from skyfield.api import wgs84, load
from datetime import timedelta

MIN_ELEVATION = 33.4  # Minimum viable elevation for the 1500km FireSat swath at 587km altitude

def fetch_satellite_data(url='https://celestrak.org/NORAD/elements/gp.php?CATNR=63256'):
    """Fetch the latest TLE data from Celestrak for FIRESAT 0."""
    satellites = load.tle_file(url)
    if satellites:
        return satellites[0]
    return None

def calculate_suitability_index(elevation_deg):
    """
    Calculate Suitability Index (S) using a trigonometric normalization
    to account for geometric distortion and atmospheric path length.
    
    S = ((sin(el) - sin(el_min)) / (1 - sin(el_min)))^1.2
    where el_min = 33.4 degrees.
    """
    el_rad = np.radians(elevation_deg)
    el_min_rad = np.radians(MIN_ELEVATION)
    
    sin_el = np.sin(el_rad)
    sin_el_min = np.sin(el_min_rad)
    
    if sin_el < sin_el_min:
        return 0.0
        
    s = ((sin_el - sin_el_min) / (1.0 - sin_el_min)) ** 1.2
    return round(float(s), 3)

def calculate_passes(satellite, lat, lon, days):
    """
    Calculate imaging passes for a given satellite, location, and time range.
    Returns a list of dictionaries with pass details.
    """
    ts = load.timescale()
    t0 = ts.now()
    t1 = ts.utc(t0.utc_datetime() + timedelta(days=days))
    
    # Define the observer location
    observer = wgs84.latlon(lat, lon)
    
    # Calculate passes
    t, events = satellite.find_events(observer, t0, t1, altitude_degrees=MIN_ELEVATION)
    
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
                
                # Only save passes that actually cross the minimum elevation threshold 
                if current_pass.get('max_elevation', 0) >= MIN_ELEVATION:
                    current_pass['duration_seconds'] = duration_seconds
                    current_pass['suitability_index'] = calculate_suitability_index(current_pass['max_elevation'])
                    passes.append(current_pass)
            current_pass = {}
            
    return passes
