import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd

st.set_page_config(page_title="Sochi Trading Stars", layout="wide")

st.title("🛰 Анализ Карак для Трейдинга (v2.1)")

def get_karakas(dt_utc):
    ts = load.timescale()
    eph = load('de421.bsp')
    t = ts.utc(dt_utc.year, dt_utc.month, dt_utc.day, dt_utc.hour, dt_utc.minute)
    
    planets = {
        'Sun': eph['sun'], 'Mars': eph['mars'], 'Mercury': eph['mercury'],
        'Jupiter': eph['jupiter_barycenter'], 'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter'],
        'Moon': eph['moon']
    }
    
    data = []
    for name, obj in planets.items():
        pos = eph['earth'].at(t).observe(obj).ecliptic_latlon()[1].degrees
        deg_in_sign = pos % 30  # Градус внутри знака (0-30)
        data.append({'Planet': name, 'Deg': deg_in_sign})
    
    # Сортировка по убыванию градуса для определения Карак
    df_sorted = pd.DataFrame(data).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    
    karaka_names = ['Atmakaraka (AK)', 'Amatyakaraka (AmK)', 'Bhratrukaraka (BK)', 
                    'Matrukaraka (MK)', 'Putrakaraka (PK)', 'Gnatikaraka (GK)', 'Darakaraka (DK)']
    
    df_sorted['Role'] = karaka_names
    return df_sorted

# Интерфейс
col1, col2 = st.columns([1, 2])
with col1:
    st.subheader("Настройки")
    date_input = st.date_input("Выберите дату", datetime.now())
    st.info("Расчет ведется на 10:00 (МСК/Сочи)")

# Получаем данные
df_final = get_karakas(datetime.combine(date_input, datetime.min.time()) - timedelta(hours=3))

with col2:
    st.subheader(f"Иерархия планет на {date_input}")
    st.table(df_final[['Role', 'Planet', 'Deg']])

st.warning("Внимание: Смена Атмакараки (верхняя строчка) часто совпадает с сильными движениями на графиках MT5.")
