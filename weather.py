# weather.py
import requests
from datetime import datetime, timedelta
import pandas as pd
import matplotlib.pyplot as plt
import io

def get_latitude_longitude(location):
    geo_api = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1"
    r = requests.get(geo_api, timeout=10)
    r.raise_for_status()
    data = r.json()
    if "results" not in data or len(data["results"]) == 0:
        raise ValueError("City not found")
    return data["results"][0]["latitude"], data["results"][0]["longitude"]

def get_past_n_days_max_min_temperature(latitude, longitude, days):
    today = datetime.utcnow().date()
    start_date = (today - timedelta(days=days)).strftime("%Y-%m-%d")
    end_date = today.strftime("%Y-%m-%d")
    temp_url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={latitude}&longitude={longitude}"
        f"&start_date={start_date}&end_date={end_date}"
        f"&daily=temperature_2m_max,temperature_2m_min&timezone=UTC"
    )
    r = requests.get(temp_url, timeout=10)
    r.raise_for_status()
    data = r.json()
    if "daily" not in data:
        raise ValueError("No daily data returned")
    return data["daily"]

def json_to_dataframe(data):
    df = pd.DataFrame({
        "date": data["time"],
        "max_temp": data["temperature_2m_max"],
        "min_temp": data["temperature_2m_min"]
    })
    df["date"] = pd.to_datetime(df["date"])
    df["avg_temp"] = (df["max_temp"] + df["min_temp"]) / 2
    return df

def create_plot_image_bytes(df, location):
    plt.ioff()
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df["date"], df["max_temp"], marker="o", label="Max")
    ax.plot(df["date"], df["min_temp"], marker="o", label="Min")
    ax.plot(df["date"], df["avg_temp"], linestyle="--", marker="o", label="Avg")
    ax.set_xlabel("Date")
    ax.set_ylabel("Temperature (°C)")
    ax.set_title(f"{location} Temperature — Past {len(df)} Days")
    ax.legend()
    fig.autofmt_xdate()
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf
