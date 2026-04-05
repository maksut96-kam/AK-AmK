import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta, time
import pandas as pd
import math
import base64

# ПРАВИЛО 1: Настройка страницы — самая первая команда
st.set_page_config(page_title="Astro Coordination Center", layout="wide")

@st.cache_resource
def init_engine():
    ts = load.timescale()
    # Прямая загрузка эфемерид
    eph = load('de421.bsp')
    return ts, eph

ts, eph = init_engine()

# --- СЛОВАРИ ---
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]
NAK_LORDS = ["Кету", "Венера", "Солнце", "Луна", "Марс", "Раху", "Юпитер", "Сатурн", "Меркурий"] * 3
P_ICONS = {'Sun': '☀️ Sun', 'Moon': '🌙 Moon', 'Mars': '🔴 Mars', 'Mercury': '☿️ Merc', 'Jupiter': '🔵 Jup', 'Venus': '♀️ Venus', 'Saturn': '🪐 Sat'}

# --- МАТЕМАТИКА ---
def get_dynamic_ayanamsa(t):
    T = (t.tt - 2451545.0) / 36525.0
    return 23.856235 + (2.30142 * T) + (0.000139 * T**2)

def get_planet_data(t):
    ayan = get_dynamic_ayanamsa(t)
    earth = eph['earth']
    planets = {'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 'Mercury': eph['mercury'], 'Jupiter': eph['jupiter_barycenter'], 'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']}
    res = []
    for name, obj in planets.items():
        lon = (earth.at(t).observe(obj).ecliptic_latlon()[1].degrees - ayan) % 360
        res.append({'Planet': name, 'Lon': lon, 'Deg': lon % 30})
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    df['Role'] = ['AK', 'AmK', 'BK', 'MK', 'PiK', 'GK', 'DK'][:len(df)]
    # Расчет Раху
    m_lon = earth.at(t).observe(eph['moon']).ecliptic_latlon()[1].degrees
    ra_lon = (m_lon - ayan + 180) % 360
    return df, 30 - (ra_lon % 30)

# ============================================================
# 🚀 ГЛАВНЫЙ ИНТЕРФЕЙС (БЕЗ УСТАРЕВШИХ КОМАНД)
# ============================================================

try:
    # 1. Считаем данные сразу
    now_utc = datetime.utcnow()
    t_now = ts.utc(now_utc.year, now_utc.month, now_utc.day, now_utc.hour, now_utc.minute, now_utc.second)
    df_main, ra_deg = get_planet_data(t_now)

    # 2. Отрисовка вкладок
    tab1, tab2 = st.tabs(["📊 Эфир", "📅 План"])

    with tab1:
        # Модуль Раху — используем новые стандартные алерты вместо HTML
        if ra_deg < 2 or ra_deg > 28:
            st.error(f"🐲 РАХУ: {ra_deg:.2f}° — ГАНДАНТА (ХАОС)")
        elif ra_deg < 5 or ra_deg > 25:
            st.warning(f"🐲 РАХУ: {ra_deg:.2f}° — ПОВЫШЕННЫЙ РИСК")
        else:
            st.success(f"🐲 РАХУ: {ra_deg:.2f}° — ТЕХНИЧНОСТЬ")

        st.divider()

        # Таблица карак — используем width='stretch' согласно логам
        st.subheader("Текущие Карак-позиции")
        df_display = df_main.copy()
        df_display['Знак'] = df_display['Lon'].apply(lambda x: ZODIAC_SIGNS[int(x/30)])
        df_display['Градус'] = df_display['Deg'].apply(lambda x: f"{x:.2f}°")
        
        st.dataframe(
            df_display[['Role', 'Planet', 'Знак', 'Градус']], 
            width='stretch', # Замена use_container_width по логам 2026
            hide_index=True
        )

        st.divider()
        
        # Информер ротаций
        ak = df_main.iloc[0]['Planet']
        amk = df_main.iloc[1]['Planet']
        st.info(f"💎 Сейчас: АК {ak} / AmK {amk}")

    with tab2:
        st.header("Планировщик")
        st.write("Выберите даты для формирования бланка.")
        start_d = st.date_input("Начало", datetime.now())
        if st.button("Начать расчет"):
            st.write("Инициализация циклов...")

except Exception as e:
    st.error(f"Системная ошибка: {e}")
