"""Smart Traffic Prediction - Streamlit UI.   Run:  streamlit run app.py"""
import json, os, joblib
import pandas as pd
import streamlit as st
from features import make_row, forecast_day, DAYS, LEVELS
from live_data import now_local, get_live_weather, get_live_traffic_level

st.set_page_config(page_title="Smart Traffic Prediction", page_icon="🚦", layout="centered")

# ---------------------------------------------------------------- load model
@st.cache_resource
def load_models():
    clf = joblib.load("models/best_model.pkl")
    reg = joblib.load("models/delay_regressor.pkl")
    meta = json.load(open("models/meta.json"))
    return clf, reg, meta

try:
    clf, reg, meta = load_models()
except Exception as e:
    st.title("🚦 Smart Traffic Prediction System")
    st.error("Could not load the trained model. Stop the app (Ctrl + C), run `python train.py` in this folder, then start the app again.")
    st.code(str(e))
    st.stop()

choices = meta["choices"]

def rerun():
    try:
        st.rerun()
    except AttributeError:          # older Streamlit
        st.experimental_rerun()

# ---------------------------------------------------------------- header
st.title("🚦 Smart Traffic Prediction System")
st.caption("Model in use: **" + meta["best_model"] + "**  |  inputs: time, day, weather, area, holiday, event, previous traffic")

mode = st.radio("Mode", ["Live (automatic)", "Manual / what-if"], horizontal=True)
live = mode.startswith("Live")
area = st.selectbox("Road / Area", choices["Area"])

# ---------------------------------------------------------------- inputs
if live:
    now = now_local()
    hour, day = now.hour, DAYS[now.weekday()]

    w = get_live_weather()
    if w:
        weather, weather_label = w["weather"], "Weather (live)"
    else:
        weather = st.selectbox("Weather (live feed unavailable - please choose)", choices["Weather"])
        weather_label = "Weather"

    try:
        tomtom_key = st.secrets["TOMTOM_KEY"]
    except Exception:
        tomtom_key = None
    tt = get_live_traffic_level(area, key=tomtom_key)
    if tt:
        prev, source = tt[0], "live road speed = " + format(tt[1], ".0%") + " of free-flow speed"
    else:
        prev = st.selectbox("Traffic you see right now", LEVELS, index=1)
        source = "entered by you"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Time", now.strftime("%H:%M"))
    c2.metric("Day", day)
    c3.metric(weather_label, weather)
    c4.metric("Current traffic", prev)
    st.caption("Current traffic source: " + source)
    if st.button("Refresh live data"):
        rerun()
else:
    c1, c2 = st.columns(2)
    hour = c1.slider("Hour of day", 0, 23, 8)
    day = c1.selectbox("Day of week", DAYS)
    weather = c2.selectbox("Weather", choices["Weather"])
    prev = c2.selectbox("Previous traffic", LEVELS, index=2)

h1, h2 = st.columns(2)
holiday = "Yes" if h1.checkbox("Public holiday") else "No"
event = "Yes" if h2.checkbox("Event nearby (match, festival, rally)") else "No"

# ---------------------------------------------------------------- prediction
row = make_row(hour, day, weather, area, holiday, event, prev)
pred = str(clf.predict(row)[0])
delay = max(0.0, float(reg.predict(row)[0]))
icon = {"Low": "🟢", "Medium": "🟡", "High": "🔴"}[pred]
box = {"Low": st.success, "Medium": st.warning, "High": st.error}[pred]
box("Predicted traffic: " + icon + " **" + pred.upper() + "**   |   Expected extra delay: **~" + str(round(delay)) + " min per 10 km**")

if hasattr(clf, "predict_proba"):
    proba = pd.Series(clf.predict_proba(row)[0], index=list(clf.classes_)).reindex(LEVELS)
    st.caption("Prediction confidence")
    st.bar_chart(proba, height=180)

advice = {"Low": "Roads are clear - good time to travel.",
          "Medium": "Moderate traffic - allow some extra time.",
          "High": "Heavy congestion expected - consider another route or time."}
st.info(advice[pred])

# ---------------------------------------------------------------- 24-hour forecast
st.subheader("Forecast for " + day + " - " + area)
try:
    fc = forecast_day(clf, reg, day, weather, area, holiday, event)
    st.line_chart(fc.set_index("Hour")["Expected_Delay_min"], height=220)
    high = fc.loc[fc["Predicted_Level"] == "High", "Hour"].tolist()
    st.write("**High traffic expected at:** " + (", ".join(str(h) + ":00" for h in high) if high else "no hour (a calm day)"))
except Exception as e:
    st.warning("Forecast not available: " + str(e))

# ---------------------------------------------------------------- performance
with st.expander("Model performance and figures"):
    if os.path.exists("figures/model_comparison.csv"):
        st.dataframe(pd.read_csv("figures/model_comparison.csv"))
    for f in ["figures/05_model_comparison.png", "figures/03_heatmap.png"]:
        if os.path.exists(f):
            st.image(f)
