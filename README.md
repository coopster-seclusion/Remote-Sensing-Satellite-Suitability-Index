# Remote-Sensing-Satellite-Suitability-Index

A Streamlit-powered decision support tool that ranks satellite imaging windows for specific coordinates, prioritizing high-elevation overpasses to ensure maximum sensor resolution.

## FireSat (Muon Space) Imaging Windows - MVP

A simple, fast web application to predict overhead optical/IR imaging passes for the **FIRESAT 0 (MUSAT-4)** satellite (NORAD ID: 63256) over any specific geographic location (e.g., active fire incidents). 
This tool is built for geospatial data pipelines, providing robust temporal resolution formats (ISO-8601 UTC) that can be easily plugged into tools like GeoPandas.

### Technical Implementation & Sensor Constraints

FireSat-0 acts as the FireSat Pathfinder with the following sensor capabilities:
- **Spatial Resolution:** Targets 5m x 5m (significantly higher than VIIRS at 375m or MODIS at 1km).
- **Sensor Type:** 6-band multispectral infrared (IR) instrument.
- **Orbit Profile:** Sun-Synchronous Orbit (SSO) at ~587 km altitude, 97.7° inclination, traveling at ~7.56 km/s.
- **Swath Width:** 1,500 km swath on the ground.

**Why this matters for the prediction logic:**
With a 1,500 km swath from a ~587 km altitude, the satellite has a very wide field of view. To guarantee a designated ground target is within this 1,500 km observing width during a pass, the application enforces a strict **~33.4° minimum elevation angle** above the horizon. Overpasses below this angle are filtered out as they do not provide valid imaging coverage of the target.

## Installation

1. Ensure Python 3.8+ is installed.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the Streamlit app:
   ```bash
   python -m streamlit run app.py
   ```
   *(Note: using `python -m streamlit run app.py` ensures it runs even if the Streamlit executable isn't on your system's PATH)*
2. The web frontend will open in your default browser automatically (`http://localhost:8501`).
3. Input the **latitude** and **longitude** of your target.
4. Select the forecast range (up to 14 days) and your local timezone.
5. Click **Predict Passes**.

## Outputs
The app outputs a table of viable satellite passes containing:
- **Rise Time (Local):** Local timestamp for the start of the pass.
- **Max Elevation:** The peak elevation of the satellite during the pass.
- **Duration:** How long the pass lasts in seconds.
- **Quality Score:** A suitability index normalized between 0-1, based equally on the maximum elevation (higher is better) and duration (longer is better) of the pass.
- **Pass Start/Peak/End (UTC ISO-8601):** Standardized, machine-readable datetime strings. Perfect for indexing in GeoPandas via `pd.to_datetime(...)`.

You can download this table as a CSV directly from the application.

### Visualizations
The app automatically generates dynamic visual outputs using the Matplotlib library:
- **Timeline Scatter Plot:** A timeline displaying all valid imaging windows over the requested forecast range. Circle size and color represent the `Quality Score` (darker/larger = better). The single most optimal pass is directly annotated.
- **Quality Comparison Plot:** Scatter plot showing the relationship between Max Elevation and Pass Duration.

All visualizations are fully interactive and adjust dynamically to the constraints provided.

## Next Phases / Roadmap

- [x] **Suitability Index Generation:** Score each pass based on exact max elevation and pass duration.
- [ ] **Data Pipeline Integration:** Connect output CSV directly to GeoPandas automated workflows.
- [ ] **Multi-Satellite Support:** Expand from FireSat-0 to track the full FireSat constellation as more satellites launch (planned for 50+ satellites by 2030).
- [ ] **Cloud Cover API Integration:** Cross-reference passes with location-specific weather forecasts to weed out obscured optical passes.
