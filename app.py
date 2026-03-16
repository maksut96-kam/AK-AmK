import streamlit as st
from skyfield.api import load, Topos
from datetime import datetime, timedelta
import pandas as pd

st.set_page_config(page_title="Planetary Cycles Sochi", layout="wide")

st.title("🛰 Расчет планетных циклов (v2.0)")
st.write("Метод: Skyfield (Pure Python) — Стабильная сборка")

# Настройки времени для Сочи
UTC_OFFSET = 3 

def get_planet_positions():
    ts = load.timescale()
    eph = load('de421.bsp')
    planets = {
        'Sun': eph['sun'],
        'Moon': eph['moon'],
        'Mars': eph['mars'],
        'Mercury': eph['mercury'],
        'Jupiter': eph['jupiter_barycenter'],
        'Venus': eph['venus'],
        'Saturn': eph['saturn_barycenter']
    }
    
    now = datetime.now()
    results = []
    
    for i in range(7):
        check_date = now + timedelta(days=i)
        t = ts.utc(check_date.year, check_date.month, check_date.day)
        
        day_data = {"Дата": check_date.strftime("%d.%m.%Y")}
        for name, obj in planets.items():
            astrometric = eph['earth'].at(t).observe(obj)
            lat, lon, distance = astrometric.ecliptic_latlon()
            day_data[name] = round(lon.degrees, 2)
        results.append(day_data)
        
    return pd.DataFrame(results)

try:
    df = get_planet_positions()
    st.success(f"Часовой пояс: UTC+{UTC_OFFSET} (Сочи)")
    st.table(df)
    st.info("Это базовые координаты. Как только этот код 'взлетит', я добавлю расчет Карак (Атмакарака и др.).")
except Exception as e:
    st.error(f"Ошибка расчета: {e}")
