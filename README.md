# 🏎️ F1 Time Ratio Dataset Generator

## Overview
This data pipeline was built to extract, clean, and preprocess Formula 1 race and qualifying data. The primary purpose is to generate a fully normalized mathematical matrix designed for a custom C++ Ordinary Least Squares (OLS) linear regression engine. 

The script fetches historical data (2020–2026) and calculates the **Final Time Ratio** — the proportional time gap between each driver and the race winner — which serves as the target variable for the regression model.

## 📊 Dataset Features (Matrix X)
The pipeline processes raw timing data and weather conditions into the following machine-learning-ready features:

* **Qualifying Performance:** Grid position, Qualifying gap ratio (to pole position).
* **Track Conditions:** Track temperature, Air temperature, Rain occurrence (boolean).
* **Historical Form:** Driver form (5-race rolling average), Team form (5-race rolling average).
* **Reliability:** Driver DNF (Did Not Finish) rate.
* **Circuit Topology:** One-Hot Encoded location data (optimized to prevent the dummy variable trap during matrix QR decomposition).

🎯 **Target Variable (Y):** Final Time Ratio.

## 📜 How it Works
Using the [FastF1](https://github.com/theOehrly/Fast-F1) library, the script automatically:
1. Downloads session data from F1 qualifying and race sessions.
2. Merges timing data with weather conditions and historical standings.
3. Filters out anomalies and calculates rolling performance metrics.
4. Normalizes all feature columns to a `0.0 - 1.0` scale.
5. Exports a clean `CSV` matrix ready for low-level matrix operations.

## 💻 Build & Run
To start generating the dataset, open your terminal in the root project directory and run:

```bash
# 1. Create and activate a Virtual Environment
python -m venv venv
source venv/bin/activate  # On native Windows use: venv\Scripts\activate

# 2. Install required dependencies
pip install -r requirements.txt

# 3. Execute the pipeline
python main.py