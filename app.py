import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd
import time

st.set_page_config(page_title="Jyotish Live Terminal", layout="wide")

# Константа Айанамсы Лахири (24г 13м 32с конвертируем в десятичные градусы)
LAHIRI_AYANAMSA = 24 + (13/60) + (32/3600)

ZODIAC_SIGNS = [
    "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", 
    "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"
]

def get_zodiac_sign(degrees):
    return ZODIAC_SIGNS[int(degrees / 30)]

def get_data():
    ts = load.timescale()
    eph = load('de421.bsp')
    
    # Берем текущее время UTC+3 (Сочи)
    now_sochi = datetime.utcnow() + timedelta(hours=3)
    utc_time = now_sochi - timedelta(hours=3)
    
    t = ts.utc(utc_time.year, utc_time.month, utc_time.day, utc_time.hour, utc_time.minute, utc_time.second)
    
    planets_map = {
        'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 
        'Mercury': eph['mercury'], 'Jupiter': eph['jupiter_barycenter'], 
        'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']
    }
    
    results = []
    for name, obj in planets_map.items():
        # Тропическая долгота
        tropical_lon = eph['earth'].at(t).observe(obj).ecliptic_latlon()[1].degrees
        
        # Сидерическая долгота (Джйотиш)
        sidereal_lon = (tropical_lon - LAHIRI_AYANAMSA) % 360
        
        deg_in_sign = sidereal_lon % 30
        sign_name = get_zodiac_sign(sidereal_lon)
        
        results.append({
            'Planet': name,
            'Sign': sign_name,
            'Deg': round(deg_in_sign, 5)
        })
    
    # Сортировка для определения Карак
    df = pd.DataFrame(results).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    karakas = ['AK', 'AmK', 'BK', 'MK', 'PK', 'GK', 'DK']
    df['Role'] = karakas
    
    return df, now_sochi

st.title("🏹 Джйотиш-Терминал: Сидерический Зодиак (Лахири)")
st.write(f"Текущая Айанамса: {round(LAHIRI_AYANAMSA, 4)}°")

# Создаем пустое место для динамического контента
placeholder = st.empty()

# Запускаем цикл обновления
while True:
    df_live, time_now = get_data()
    
    with placeholder.container():
        st.subheader(f"🕒 Время в Сочи: {time_now.strftime('%H:%M:%S')}")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            st.dataframe(df_live[['Role', 'Planet', 'Sign', 'Deg']], use_container_width=True)
        
        with col2:
            ak_planet = df_live.iloc[0]
            st.metric("Atmakaraka (AK)", ak_planet['Planet'], f"{ak_planet['Sign']} {round(ak_planet['Deg'], 2)}°")
            st.info("Данные обновляются в реальном времени...")

    time.sleep(1) # Пауза в 1 секунду перед следующим обновлением
