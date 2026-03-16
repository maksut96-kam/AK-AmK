import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd
import time
import streamlit.components.v1 as components

# 1. Настройка и статический заголовок (не меняется)
st.set_page_config(page_title="Max Pro-Trader Coordination center", layout="wide")

st.markdown("<h1 style='text-align: center; margin-bottom: 0;'>Max Pro-Trader Coordination center</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray; font-size: 0.8em;'>v4.9 Build | Owner: Max | System Area: Sochi (UTC+3)</p>", unsafe_allow_html=True)

# Константы Накшатр
LAHIRI_AYANAMSA = 24.2255
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS_DB = [
    ("Ашвини", "Кету", "Резкий старт"), ("Бхарани", "Венера", "Напряжение"), ("Криттика", "Солнце", "Прорыв"),
    ("Рохини", "Луна", "Рост"), ("Мригашира", "Марс", "Поиск"), ("Аридра", "Раху", "Хаос"),
    ("Пунарвасу", "Юпитер", "Отскок"), ("Пушья", "Сатурн", "Стабильность"), ("Ашлеша", "Меркурий", "Ловушка"),
    ("Магха", "Кету", "Традиция"), ("Пурва-пх", "Венера", "Пауза"), ("Уттара-пх", "Солнце", "Успех"),
    ("Хаста", "Луна", "Точность"), ("Читра", "Марс", "Структура"), ("Свати", "Раху", "Ветер"),
    ("Вишакха", "Юпитер", "Цель"), ("Анурадха", "Сатурн", "Скрытое"), ("Джьештха", "Меркурий", "Мастерство"),
    ("Мула", "Кету", "Крах"), ("Пурва-аш", "Венера", "Оптимизм"), ("Уттара-аш", "Солнце", "Победа"),
    ("Шравана", "Луна", "Инсайд"), ("Дхаништха", "Марс", "Импульс"), ("Шатабхиша", "Раху", "Манипуляция"),
    ("Пурва-бх", "Юпитер", "Жертва"), ("Уттара-бх", "Сатурн", "Глубина"), ("Ревати", "Меркурий", "Финал")
]

def get_planet_data(t, eph):
    planets = {'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 'Mercury': eph['mercury'], 
               'Jupiter': eph['jupiter_barycenter'], 'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']}
    res = []
    for name, obj in planets.items():
        lon = (eph['earth'].at(t).observe(obj).ecliptic_latlon()[1].degrees - LAHIRI_AYANAMSA) % 360
        res.append({'Planet': name, 'Lon': lon, 'Deg': lon % 30})
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    df.index += 1
    return df

# --- БЛОК НЕДЕЛЬНОГО ПЛАНИРОВАНИЯ (Статичный, над циклом) ---
st.subheader("📅 Weekly Strategy Coordination")
with st.expander("Открыть план на неделю для печати и прогнозов с Юлей"):
    ts_w = load.timescale()
    eph_w = load('de421.bsp')
    base_date = datetime.utcnow() + timedelta(hours=3)
    weekly_list = []
    
    for i in range(7):
        day = base_date + timedelta(days=i)
        t_w = ts_w.utc(day.year, day.month, day.day, 12, 0)
        df_w = get_planet_data(t_w, eph_w)
        ak_w, amk_w = df_w.iloc[0], df_w.iloc[1]
        nak_w = NAKSHATRAS_DB[int(ak_w['Lon'] / (360/27)) % 27]
        weekly_list.append({
            "Дата": day.strftime("%d.%m"), "AK/AmK": f"{ak_w['Planet']}/{amk_w['Planet']}",
            "Накшатра AK": nak_w[0], "Характер": nak_w[2], "Прогноз (Max/Юля)": "________________"
        })
    st.table(pd.DataFrame(weekly_list))
    
    components.html("""
        <script>function printPage() { window.print(); }</script>
        <button onclick="printPage()" style="width:100%; height:40px; background:#4CAF50; color:white; border:none; border-radius:8px; cursor:pointer;">
            🖨 ПЕЧАТЬ ПЛАНА (CTRL+P)
        </button>
    """, height=50)

st.divider()

# --- БЛОК REAL-TIME (Живой) ---
st.subheader("📊 Real-time Planetary Flow")
placeholder = st.empty()

ts = load.timescale()
eph = load('de421.bsp')

while True:
    now_sochi = datetime.utcnow() + timedelta(hours=3)
    t_now = ts.utc(now_sochi.year, now_sochi.month, now_sochi.day, now_sochi.hour, now_sochi.minute, now_sochi.second)
    df_now = get_planet_data(t_now, eph)
    ak = df_now.iloc[0]
    nak_info = NAKSHATRAS_DB[int(ak['Lon'] / (360/27)) % 27]

    with placeholder.container():
        c1, c2 = st.columns([1, 3])
        c1.metric("Time Sochi", now_sochi.strftime('%H:%M:%S'))
        c2.info(f"🎙 **Voice of Stars:** AK {ak['Planet']} в {nak_info[0]} — {nak_info[2]}")
        
        st.dataframe(df_now[['Planet', 'Deg']], use_container_width=True)
    
    time.sleep(1)
