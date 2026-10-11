# Real-Time Implementation Guide

## Why vehicle count was removed
Nobody types "450 vehicles" into an app. We now use inputs that are **known automatically or visible to any commuter**:

| Input | Where it comes from in real time |
|---|---|
| Hour, Day | System clock (automatic) |
| Weather | Open-Meteo API - free, no key (automatic) |
| Area / road | User picks from a dropdown |
| Previous / current traffic | TomTom Traffic API live speed (automatic), or the user picks what they see |
| Public holiday, Event nearby | Two checkboxes |
| (derived) Time_Slot, Is_Weekend, Hour_sin/cos | Computed in `features.py` |

The model also predicts **Delay_Minutes** (extra minutes for a 10 km trip) with Linear Regression. Delay can be measured from any maps travel-time API, so a real dataset can be collected.

## Architecture
```
Clock + Open-Meteo weather + (TomTom live speed)  ->  live_data.py
                         |
                 features.py (same code as training)
                         |
        best_model.pkl -> Low / Medium / High   +   delay_regressor.pkl -> minutes
                         |
                 Streamlit UI (Live mode) + 24-hour forecast
```

## What works now (tested vs not tested)
- Clock, feature engineering, model prediction, 24-hour forecast: tested.
- Open-Meteo weather: coded with a safe fallback. If the internet or API fails, the app asks the user to pick the weather. I could not test the live call from my environment, so check it on your Mac (the Weather tile shows "(live)" when it works).
- TomTom live traffic: optional and untested. Without a key the app asks "Traffic you see right now".

## Turn on TomTom live traffic (optional, free tier)
1. Create a free account at developer.tomtom.com and copy an API key.
2. Edit `AREA_POINTS` in `live_data.py` with a real road coordinate for each area, and `CITY_LAT/LON`, `TZ`.
3. Local run: `export TOMTOM_KEY="your_key"` then `streamlit run app.py`.
4. Streamlit Cloud: App settings -> Secrets -> add `TOMTOM_KEY = "your_key"`.

## Going fully real-time later (future work to mention)
1. Log live speed + weather every 15 min into a CSV/database (a scheduled script).
2. After a few weeks, retrain `train.py` on that real data.
3. Replace the synthetic CSV; no other code changes are needed.
4. Add forecast weather (Open-Meteo hourly) so the 24-hour chart uses future weather.

## How to explain it in the viva
"Instead of asking users for a vehicle count, we use inputs available in real time: the clock, a free weather API and, optionally, live road speed. The same feature code is used in training and in the app, so predictions are consistent."
