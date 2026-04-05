import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta, time
import pandas as pd
import math
import base64

# 1. ПЕРВООЧЕРЕДНАЯ НАСТРОЙКА
st.set_page_config(page_title="Julia Astro Assistant", layout="wide")

@st.cache_resource
def init_engine():
    ts = load.timescale()
    # Загружаем эфемериды (Streamlit сам подтянет их, если есть интернет)
    eph = load('de421.bsp')
    return ts, eph

ts, eph = init_engine()

# --- КОНСТАНТЫ И СЛОВАРИ ---
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]
NAK_LORDS = ["Кету", "Венера", "Солнце", "Луна", "Марс", "Раху", "Юпитер", "Сатурн", "Меркурий"] * 3
P_ICONS = {'Sun': '☀️ Sun', 'Moon': '🌙 Moon', 'Mars': '🔴 Mars', 'Mercury': '☿️ Merc', 'Jupiter': '🔵 Jup', 'Venus': '♀️ Venus', 'Saturn': '🪐 Sat'}

# --- МАТЕМАТИЧЕСКИЕ ФУНКЦИИ ---
def get_dynamic_ayanamsa(t):
    T = (t.tt - 2451545.0) / 36525.0
    return 23.856235 + (2.30142 * T) + (0.000139 * T**2)

def get_full_info(row):
    nak_idx = int(row['Lon'] / (360/27)) % 27
    sign = ZODIAC_SIGNS[int(row['Lon'] / 30)]
    return f"{P_ICONS.get(row['Planet'], row['Planet'])} | {sign} | {NAKSHATRAS[nak_idx]}"

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

def get_lunar_info(t):
    s_lon = eph['earth'].at(t).observe(eph['sun']).ecliptic_latlon()[1].degrees
    m_lon = eph['earth'].at(t).observe(eph['moon']).ecliptic_latlon()[1].degrees
    diff = (m_lon - s_lon) % 360
    tithi = math.ceil(diff / 12) or 1
    status = "Растущая" if diff < 180 else "Убывающая"
    return tithi, status

# ============================================================
# 🚀 ГЛАВНЫЙ ИНТЕРФЕЙС
# ============================================================
try:
    # Предварительный расчет (вне вкладок для стабильности)
    now_utc = datetime.utcnow()
    t_now = ts.utc(now_utc.year, now_utc.month, now_utc.day, now_utc.hour, now_utc.minute, now_utc.second)
    df_main, ra_deg = get_planet_data(t_now)
    tithi, phase = get_lunar_info(t_now)

    tab1, tab2 = st.tabs(["📊 Прямой эфир", "📅 Планировщик"])

    with tab1:
        # Модуль Раху (упрощенный стиль)
        if ra_deg < 2 or ra_deg > 28:
            st.error(f"🐲 РАХУ: {ra_deg:.2f}° — КРИТИЧЕСКИЙ ХАОС (ГАНДАНТА)")
        elif ra_deg < 5 or ra_deg > 25:
            st.warning(f"🐲 РАХУ: {ra_deg:.2f}° — ПОВЫШЕННЫЙ РИСК")
        else:
            st.success(f"🐲 РАХУ: {ra_deg:.2f}° — ТЕХНИЧНЫЙ РЫНОК")
        
        st.divider()
        
        col1, col2 = st.columns(2)
        col1.metric("Лунные сутки", f"{tithi}")
        col2.metric("Фаза", phase)

        st.divider()

        # Таблица карак
        st.subheader("Таблица Чара-карак")
        df_display = df_main.copy()
        df_display['Знак'] = df_display['Lon'].apply(lambda x: ZODIAC_SIGNS[int(x/30)])
        df_display['Градус'] = df_display['Deg'].apply(lambda x: f"{x:.2f}°")
        # Используем современный st.dataframe вместо st.table
        st.dataframe(df_display[['Role', 'Planet', 'Знак', 'Градус']], use_container_width=True)

        st.divider()

        # Ротации
        st.subheader("🔄 Ближайшие ротации")
        ak_now = df_main.iloc[0]['Planet']
        amk_now = df_main.iloc[1]['Planet']
        
        # Поиск следующей смены
        found = False
        for m in range(10, 1440, 10):
            future_t = now_utc + timedelta(minutes=m)
            t_check = ts.utc(future_t.year, future_t.month, future_t.day, future_t.hour, future_t.minute)
            df_check, _ = get_planet_data(t_check)
            if df_check.iloc[0]['Planet'] != ak_now or df_check.iloc[1]['Planet'] != amk_now:
                st.info(f"Смена через {m} мин: {(future_t + timedelta(hours=3)).strftime('%H:%M')} (МСК)")
                st.write(f"Будет: АК {df_check.iloc[0]['Planet']} / AmK {df_check.iloc[1]['Planet']}")
                found = True
                break
        if not found: st.write("В ближайшие 24 часа смен не ожидается.")

    with tab2:
        st.header("Планировщик")
        st.write("Выберите диапазон для расчета бланка.")
        d_start = st.date_input("Дата начала", datetime.now())
        if st.button("Рассчитать периоды"):
            st.write("Функция расчета активирована. Проверка циклов...")
            # Логика планировщика будет здесь

except Exception as e:
    st.error(f"Произошла ошибка: {e}")
