import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta, time
import pandas as pd
import streamlit.components.v1 as components
import math
import os
import base64

# ============================================================
# ⛔ БЛОК 1: ФУНДАМЕНТ (БАЗОВЫЕ НАСТРОЙКИ И ДВИЖОК)
# ============================================================
st.set_page_config(page_title="Julia Assistant Astro Coordination Center", layout="wide")

@st.cache_resource
def init_engine():
    ts = load.timescale()
    eph = load('de421.bsp')
    return ts, eph

ts, eph = init_engine()

# --- СЛОВАРИ И КОНСТАНТЫ ---
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]
NAK_LORDS = ["Кету", "Венера", "Солнце", "Луна", "Марс", "Раху", "Юпитер", "Сатурн", "Меркурий"] * 3
P_ICONS = {'Sun': '☀️ Sun', 'Moon': '🌙 Moon', 'Mars': '🔴 Mars', 'Mercury': '☿️ Merc', 'Jupiter': '🔵 Jup', 'Venus': '♀️ Venus', 'Saturn': '🪐 Sat'}
Z_ICONS = {"Овен": "♈ Овен", "Телец": "♉ Телец", "Близнецы": "♊ Близн", "Рак": "♋ Рак", "Лев": "♌ Лев", "Дева": "♍ Дева", "Весы": "♎ Весы", "Скорпион": "♏Скорп", "Стрелец": "♐ Стрел", "Козерог": "♑Козег", "Водолей": "♒ Водол", "Рыбы": "♓ Рыбы"}

# ============================================================
# ⛔ БЛОК 2: МАТЕМАТИЧЕСКОЕ ЯДРО (АСТРО-ЛОГИКА)
# ============================================================
def get_dynamic_ayanamsa(t):
    T = (t.tt - 2451545.0) / 36525.0
    return 23.856235 + (2.30142 * T) + (0.000139 * T**2)

def get_planet_data(t):
    ayan = get_dynamic_ayanamsa(t)
    earth = eph['earth']
    planets_objects = {'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 'Mercury': eph['mercury'], 'Jupiter': eph['jupiter_barycenter'], 'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']}
    res = []
    for name, obj in planets_objects.items():
        lon = (earth.at(t).observe(obj).ecliptic_latlon()[1].degrees - ayan) % 360
        res.append({'Planet': name, 'Lon': lon, 'Deg': lon % 30})
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    df['Role'] = ['AK', 'AmK', 'BK', 'MK', 'PiK', 'GK', 'DK'][:len(df)]
    ra_lon = (earth.at(t).observe(eph['moon']).ecliptic_latlon()[1].degrees - ayan + 180) % 360 
    ra_deg = 30 - (ra_lon % 30) 
    return df, ra_lon, ra_deg

def get_full_info(row):
    sign = ZODIAC_SIGNS[int(row['Lon']/30)]
    return f"{P_ICONS.get(row['Planet'], row['Planet'])} | {Z_ICONS.get(sign, sign)} {row['Deg']:.2f}°"

# ============================================================
# ⛔ БЛОК 3: ШАПКА, ЛОГОТИП И ЧАСЫ
# ============================================================
col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
with col_l2:
    if os.path.exists("logo.png"):
        st.image("logo.png", width='stretch')

st.markdown("""
<style>
    .julia-title { text-align: center; margin-top: -10px; margin-bottom: 25px; font-weight: 800; font-size: 3.2em; 
    background: linear-gradient(270deg, #0D1B2A, #1B263B, #415A77, #0D1B2A); background-size: 400% 400%; 
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: dark-glow 10s ease infinite; }
    @keyframes dark-glow { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
</style>
<h1 class="julia-title">Julia Assistant Astro Coordination Center</h1>
""", unsafe_allow_html=True)

st.iframe("""
    <div style="background: linear-gradient(90deg, #050510, #0a0a20); padding:15px; border-radius:15px; text-align:center; font-family: sans-serif; border: 1px solid #1B263B;">
        <h2 id="clock" style="margin:0; color:#415A77; letter-spacing: 2px;">Загрузка...</h2>
        <p style="margin:0; color:#778DA9; font-size: 0.8em; text-transform: uppercase;">Sochi Astro-Coordination Time (UTC+3)</p>
    </div>
    <script>
        function updateClock() { let d = new Date(); let utc = d.getTime() + (d.getTimezoneOffset() * 60000); let sochi = new Date(utc + (3600000 * 3)); document.getElementById('clock').innerHTML = sochi.toLocaleTimeString('ru-RU'); }
        setInterval(updateClock, 1000); updateClock();
    </script>
""", height=110)

# ============================================================
# ⛔ БЛОК 4: ОПЕРАТИВНЫЙ МОНИТОРИНГ (ТАБЫ)
# ============================================================
tab1, tab2 = st.tabs(["📊 Прямой эфир", "📅 Высокоточный Планировщик"])

with tab1:
    now_utc = datetime.utcnow()
    t_now = ts.utc(now_utc.year, now_utc.month, now_utc.day, now_utc.hour, now_utc.minute, now_utc.second)
    df, ra_lon, ra_deg = get_planet_data(t_now)
    
    # Модуль Раху
    if ra_deg < 2 or ra_deg > 28: color = "#FF4B4B"
    elif ra_deg < 5 or ra_deg > 25: color = "#FFA500"
    else: color = "#00C853"
    st.markdown(f"<div style='border-left:5px solid {color}; padding:10px; background:{color}11;'><h3>🐲 Раху: {ra_deg:.2f}°</h3></div>", unsafe_allow_html=True)

    st.divider()
    
    # Таблица Карак
    st.subheader("📊 Таблица Чара-карак")
    df_v = df.copy()
    df_v['Знак'] = df_v['Lon'].apply(lambda x: Z_ICONS[ZODIAC_SIGNS[int(x/30)]])
    df_v['Накшатра'] = df_v['Lon'].apply(lambda x: f"{NAKSHATRAS[int(x/(360/27))%27]} ({NAK_LORDS[int(x/(360/27))%27]})")
    df_v['Градус'] = df_v['Deg'].apply(lambda x: f"{x:.4f}°")
    st.dataframe(df_v[['Role', 'Planet', 'Знак', 'Накшатра', 'Градус']], width='stretch', hide_index=True)

    st.divider()

    # --- МОНИТОРИНГ РОТАЦИЙ (ВОССТАНОВЛЕНО) ---
    st.subheader("🔄 Мониторинг ротаций")
    ak_now, amk_now = df.iloc[0]['Planet'], df.iloc[1]['Planet']
    
    c_m1, c_m2 = st.columns(2)
    c_m1.metric("💎 Текущая АК", get_full_info(df.iloc[0]))
    c_m2.metric("🥈 Текущая AmK", get_full_info(df.iloc[1]))

    cols = st.columns(2)
    settings = [(-1, "⬅️ Предыдущая смена", "#415A77"), (1, "➡️ Следующая смена", "#778DA9")]
    for idx, (direct, label, color_lab) in enumerate(settings):
        with cols[idx]:
            st.markdown(f"<h4 style='color:{color_lab};'>{label}</h4>", unsafe_allow_html=True)
            for m in range(10, 2880, 10):
                target = now_utc + timedelta(minutes=m*direct)
                t_t = ts.utc(target.year, target.month, target.day, target.hour, target.minute)
                df_t, _, _ = get_planet_data(t_t)
                if df_t.iloc[0]['Planet'] != ak_now or df_t.iloc[1]['Planet'] != amk_now:
                    st.success(f"📅 {(target + timedelta(hours=3)).strftime('%d.%m %H:%M')}")
                    st.caption(f"АК: {get_full_info(df_t.iloc[0])} | AmK: {get_full_info(df_t.iloc[1])}")
                    break

# ============================================================
# ⛔ БЛОК 5: ПЛАНИРОВЩИК (ВЫСОКОТОЧНЫЙ РАСЧЕТ)
# ============================================================
with tab2:
    st.header("📅 Высокоточный планировщик")
    c_p1, c_p2 = st.columns(2)
    d_s = c_p1.date_input("Начало", datetime.now())
    d_e = c_p2.date_input("Конец", datetime.now() + timedelta(days=3))
    
    if st.button('🚀 Сформировать план'):
        curr_utc = datetime.combine(d_s, time(0,0)) - timedelta(hours=3)
        end_utc = datetime.combine(d_e, time(23,59)) - timedelta(hours=3)
        events = []
        
        t_init = ts.utc(curr_utc.year, curr_utc.month, curr_utc.day, curr_utc.hour, curr_utc.minute)
        df_i, _, _ = get_planet_data(t_init)
        last_pair = f"{df_i.iloc[0]['Planet']}/{df_i.iloc[1]['Planet']}"
        events.append({"Время (Сочи)": (curr_utc + timedelta(hours=3)).strftime("%d.%m %H:%M"), "АК": get_full_info(df_i.iloc[0]), "AmK": get_full_info(df_i.iloc[1])})

        while curr_utc < end_utc:
            curr_utc += timedelta(minutes=5)
            t_s = ts.utc(curr_utc.year, curr_utc.month, curr_utc.day, curr_utc.hour, curr_utc.minute)
            df_s, _, _ = get_planet_data(t_s)
            new_pair = f"{df_s.iloc[0]['Planet']}/{df_s.iloc[1]['Planet']}"
            if new_pair != last_pair:
                events.append({"Время (Сочи)": (curr_utc + timedelta(hours=3)).strftime("%d.%m %H:%M"), "АК": get_full_info(df_s.iloc[0]), "AmK": get_full_info(df_s.iloc[1])})
                last_pair = new_pair
        st.table(pd.DataFrame(events))
