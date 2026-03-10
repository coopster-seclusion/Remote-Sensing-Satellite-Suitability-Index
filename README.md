# Remote-Sensing-Satellite-Suitability-Index
A Streamlit-powered decision support tool that ranks satellite imaging windows for specific coordinates, prioritizing high-elevation overpasses to ensure maximum sensor resolution.

## FireSat Pass Predictor MVP

A simple Streamlit web application to predict overhead passes for the **FIRESAT 0 (MUSAT-4)** satellite (NORAD ID: 63256) over any specific geographic location. 
This tool is built for geospatial data, providing robust temporal resolution formats (ISO-8601 UTC) that can be easily plugged into tools like GeoPandas.

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
2. The web frontend will open in your default browser automatically.
3. Input the **latitude** and **longitude** of your target (e.g., a active fire incident).
4. Select the forecast range (up to 14 days) and your local timezone.
5. Click **Predict Passes**.

## Outputs
The app will output a table of satellite passes containing:
- **Rise Time (Local):** Local timestamp for the start of the pass.
- **Max Elevation:** The peak elevation of the satellite during the pass.
- **Duration:** How long the pass lasts in seconds.
- **Pass Start/Peak/End (UTC ISO-8601):** Standardized, machine-readable datetime strings. Perfect for indexing in GeoPandas via `pd.to_datetime(...)`.

You can also download this table as a CSV directly from the application.
