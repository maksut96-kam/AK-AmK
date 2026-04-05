import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta, time
import pandas as pd
import math
import base64

# ПЕРВАЯ КОМАНДА
st.set_page_config(page_title="Julia Astro Center", layout="wide")

@st.cache_resource
def init_engine():
    ts = load.timescale()
    # Загружаем эфемериды напрямую из надежного источника, если локального нет
    eph = load('de421.bsp')
    return ts, eph

ts, eph = init_engine()

# --- КОНСТАНТЫ ---
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]
NAK_LORDS = ["Кету", "Венера", "Солнце", "Луна", "Марс", "Раху", "Юпитер", "Сатурн", "Меркурий"] * 3
P_ICONS = {'Sun': '☀️ Sun', 'Moon': '🌙 Moon', 'Mars': '🔴 Mars', 'Mercury': '☿️ Merc', 'Jupiter': '🔵 Jup', 'Venus': '♀️ Venus', 'Saturn': '🪐 Sat'}
Z_ICONS = {s: f" {s}" for s in ZODIAC_SIGNS}

# --- МАТЕМАТИКА ---
def get_dynamic_ayanamsa(t):
    T = (t.tt - 2451545.0) / 36525.0
    return 23.856235 + (2.30142 * T) + (0.000139 * T**2)

def get_planet_data(t):
    ayan = get_dynamic_ayanamsa(t)
    planets = {'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 'Mercury': eph['mercury'], 'Jupiter': eph['jupiter_barycenter'], 'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']}
    res = []
    for name, obj in planets.items():
        lon = (eph['earth'].at(t).observe(obj).ecliptic_latlon()[1].degrees - ayan) % 360
        res.append({'Planet': name, 'Lon': lon, 'Deg': lon % 30})
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    df['Role'] = ['AK', 'AmK', 'BK', 'MK', 'PiK', 'GK', 'DK'][:len(df)]
    # Расчет Раху
    m_lon = eph['earth'].at(t).observe(eph['moon']).ecliptic_latlon()[1].degrees
    ra_lon = (m_lon - ayan + 180) % 360
    return df, 30 - (ra_lon % 30)

def get_lunar_info(t):
    s_lon = eph['earth'].at(t).observe(eph['sun']).ecliptic_latlon()[1].degrees
    m_lon = eph['earth'].at(t).observe(eph['moon']).ecliptic_latlon()[1].degrees
    diff = (m_lon - s_lon) % 360
    return math.ceil(diff / 12) or 1, "Растущая" if diff < 180 else "Убывающая"

# --- ИНТЕРФЕЙС ---
def render_rahu(ra_deg):
    color = "#FF4B4B" if (ra_deg < 2 or ra_deg > 28) else "#00C853"
    st.markdown(f"""<div style="border-left:5px solid {color}; padding:15px; background:{color}11; border-radius:10px;">
        <h2 style="margin:0; color:{color};">🐲 Раху: {ra_deg:.2f}°</h2>
        <p>Статус: {"<b>ГАНДАНТА / ХАОС</b>" if color=="#FF4B4B" else "Стабильно"}</p>
    </div>""", unsafe_allow_html=True)

# --- СБОРКА ---
try:
    now = datetime.utcnow()
    t_now = ts.utc(now.year, now.month, now.day, now.hour, now.minute, now.second)
    df, ra_deg = get_planet_data(t_now)
    tithi, phase = get_lunar_info(t_now)

    tab1, tab2 = st.tabs(["📊 Эфир", "📅 План"])

    with tab1:
        render_rahu(ra_deg)
        st.divider()
        st.subheader(f"🌙 Луна: {tithi} сутки ({phase})")
        
        # Таблица карак
        df_display = df.copy()
        df_display['Знак'] = df_display['Lon'].apply(lambda x: ZODIAC_SIGNS[int(x/30)])
        st.dataframe(df_display[['Role', 'Planet', 'Знак', 'Deg']], width="stretch")

    with tab2:
        st.info("Планировщик готов к расчету. Выберите даты.")
        if st.button("Запустить сканирование"):
            st.write("Поиск ротаций...")
            # Тут будет логика поиска (добавим, когда оживим экран)

except Exception as e:
    st.error(f"Ошибка: {e}")
