import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta, time
import pandas as pd
import math
import base64

# --- 1. ФУНДАМЕНТ ---
st.set_page_config(page_title="Julia Assistant Astro", layout="wide")

@st.cache_resource
def init_engine():
    ts = load.timescale()
    eph = load('de421.bsp')
    return ts, eph

ts, eph = init_engine()

# --- 2. СПРАВОЧНИКИ ---
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]
NAK_LORDS = ["Кету", "Венера", "Солнце", "Луна", "Марс", "Раху", "Юпитер", "Сатурн", "Меркурий"] * 3
P_ICONS = {'Sun': '☀️ Sun', 'Moon': '🌙 Moon', 'Mars': '🔴 Mars', 'Mercury': '☿️ Merc', 'Jupiter': '🔵 Jup', 'Venus': '♀️ Venus', 'Saturn': '🪐 Sat'}

# --- 3. ВЫЧИСЛЕНИЯ ---
def get_dynamic_ayanamsa(t):
    T = (t.tt - 2451545.0) / 36525.0
    return 23.856235 + (2.30142 * T) + (0.000139 * T**2)

def get_full_astro_data(t):
    ayan = get_dynamic_ayanamsa(t)
    earth = eph['earth']
    planets = {'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 'Mercury': eph['mercury'], 'Jupiter': eph['jupiter_barycenter'], 'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']}
    
    res = []
    for name, obj in planets.items():
        lon = (earth.at(t).observe(obj).ecliptic_latlon()[1].degrees - ayan) % 360
        nak_idx = int(lon / (360/27)) % 27
        res.append({
            'Planet': P_ICONS.get(name, name),
            'Sign': ZODIAC_SIGNS[int(lon/30)],
            'Nakshatra': f"{NAKSHATRAS[nak_idx]} ({NAK_LORDS[nak_idx]})",
            'Deg': lon % 30,
            'Full_Lon': lon
        })
    
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    df.insert(0, 'Role', ['AK', 'AmK', 'BK', 'MK', 'PiK', 'GK', 'DK'][:len(df)])
    
    # Раху
    m_lon = earth.at(t).observe(eph['moon']).ecliptic_latlon()[1].degrees
    ra_lon = (m_lon - ayan + 180) % 360
    ra_deg = 30 - (ra_lon % 30)
    
    # Луна
    s_lon = earth.at(t).observe(eph['sun']).ecliptic_latlon()[1].degrees
    m_lon_raw = earth.at(t).observe(eph['moon']).ecliptic_latlon()[1].degrees
    diff = (m_lon_raw - s_lon) % 360
    tithi = math.ceil(diff / 12) or 1
    phase = "Растущая" if diff < 180 else "Убывающая"
    
    return df, ra_deg, tithi, phase

# --- 4. ИНТЕРФЕЙС ---
st.title("Julia Assistant: Полная версия 2.0")

try:
    now_utc = datetime.utcnow()
    t_now = ts.utc(now_utc.year, now_utc.month, now_utc.day, now_utc.hour, now_utc.minute, now_utc.second)
    df_main, ra_deg, tithi, phase = get_full_astro_data(t_now)

    tab1, tab2 = st.tabs(["📊 Прямой эфир", "📅 Планировщик"])

    with tab1:
        # Раху
        if ra_deg < 2 or ra_deg > 28:
            st.error(f"🐲 МОНИТОР РАХУ: {ra_deg:.2f}° — ГАНДАНТА (ХАОС)")
        elif ra_deg < 5 or ra_deg > 25:
            st.warning(f"🐲 МОНИТОР РАХУ: {ra_deg:.2f}° — ПОВЫШЕННЫЙ РИСК")
        else:
            st.success(f"🐲 МОНИТОР РАХУ: {ra_deg:.2f}° — СТАБИЛЬНО")

        # Луна и Карак-пара
        c1, c2, c3 = st.columns(3)
        c1.metric("Лунные сутки", tithi)
        c2.metric("Фаза", phase)
        c3.metric("Пара АК/AmK", f"{df_main.iloc[0]['Planet']} / {df_main.iloc[1]['Planet']}")

        st.divider()
        st.subheader("Таблица Чара-карак")
        st.dataframe(df_main[['Role', 'Planet', 'Sign', 'Nakshatra', 'Deg']], width='stretch', hide_index=True)

    with tab2:
        st.header("Планировщик ротаций")
        col_p1, col_p2 = st.columns(2)
        d_s = col_p1.date_input("Начало", datetime.now())
        d_e = col_p2.date_input("Конец", datetime.now() + timedelta(days=2))
        
        if st.button("🚀 Сформировать план"):
            with st.spinner("Идет расчет..."):
                curr = datetime.combine(d_s, time(0,0)) - timedelta(hours=3)
                end = datetime.combine(d_e, time(23,59)) - timedelta(hours=3)
                
                results = []
                # Исходная точка
                t_i = ts.utc(curr.year, curr.month, curr.day, curr.hour, curr.minute)
                df_i, _, _, _ = get_full_astro_data(t_i)
                last_pair = f"{df_i.iloc[0]['Planet']}{df_i.iloc[1]['Planet']}"
                
                results.append({
                    "Время (Сочи)": (curr + timedelta(hours=3)).strftime("%d.%m %H:%M"),
                    "АК": df_i.iloc[0]['Planet'],
                    "AmK": df_i.iloc[1]['Planet'],
                    "Знак АК": df_i.iloc[0]['Sign']
                })

                while curr < end:
                    curr += timedelta(minutes=10)
                    t_s = ts.utc(curr.year, curr.month, curr.day, curr.hour, curr.minute)
                    df_s, _, _, _ = get_full_astro_data(t_s)
                    new_pair = f"{df_s.iloc[0]['Planet']}{df_s.iloc[1]['Planet']}"
                    
                    if new_pair != last_pair:
                        results.append({
                            "Время (Сочи)": (curr + timedelta(hours=3)).strftime("%d.%m %H:%M"),
                            "АК": df_s.iloc[0]['Planet'],
                            "AmK": df_s.iloc[1]['Planet'],
                            "Знак АК": df_s.iloc[0]['Sign']
                        })
                        last_pair = new_pair
                
                st.table(pd.DataFrame(results))

except Exception as e:
    st.error(f"Ошибка системы: {e}")
