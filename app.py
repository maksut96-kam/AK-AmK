import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd
import time
import streamlit.components.v1 as components

# Настройка страницы
st.set_page_config(page_title="Max Pro-Trader CC", layout="wide")

# Статичный заголовок и версия
st.markdown("<h1 style='text-align: center;'>Max Pro-Trader Coordination center</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>v4.7 Build | Last Update: 2026-03-16</p>", unsafe_allow_html=True)

# Константы
LAHIRI_AYANAMSA = 24.2255
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS_DB = [
    ("Ашвини", "Кету", "Резкое начало тренда"), ("Бхарани", "Венера", "Фиксация прибыли"),
    ("Криттика", "Солнце", "Пробитие уровней"), ("Рохини", "Луна", "Стабильный рост"),
    ("Мригашира", "Марс", "Волатильность"), ("Аридра", "Раху", "Хаос и новости"),
    # ... (здесь используется полная база из 27 накшатр)
]

def get_planet_data(t, eph):
    planets_map = {'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 'Mercury': eph['mercury'], 
                   'Jupiter': eph['jupiter_barycenter'], 'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']}
    res = []
    for name, obj in planets_map.items():
        lon = (eph['earth'].at(t).observe(obj).ecliptic_latlon()[1].degrees - LAHIRI_AYANAMSA) % 360
        res.append({'Planet': name, 'Lon': lon, 'Deg': lon % 30})
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    df.index += 1
    return df

def get_weekly_plan():
    # Упрощенная логика: расчет на 7 дней вперед с шагом 12 часов
    ts = load.timescale()
    eph = load('de421.bsp')
    start_date = datetime.utcnow() + timedelta(hours=3)
    plan_data = []
    
    for i in range(7):
        check_t = ts.utc(start_date.year, start_date.month, start_date.day + i, 12, 0)
        df_day = get_planet_data(check_t, eph)
        ak = df_day.iloc[0]['Planet']
        amk = df_day.iloc[1]['Planet']
        lon_ak = df_day.iloc[0]['Lon']
        nak_name = NAKSHATRAS_DB[int(lon_ak / (360/27)) % 27][0]
        
        plan_data.append({
            "Дата": (start_date + timedelta(days=i)).strftime("%d.%m"),
            "AK-AmK": f"{ak} / {amk}",
            "Накшатра AK": nak_name,
            "Влияние": "Влияние на тренд...", # Сюда подставим описание
            "Прогноз (Ваш)": "________________" 
        })
    return pd.DataFrame(plan_data)

# Скрипт для кнопки печати
def print_page():
    components.html("""
        <script>
            function printDiv() {
                window.print();
            }
        </script>
        <button onclick="printDiv()" style="width: 100%; height: 40px; background-color: #4CAF50; color: white; border: none; border-radius: 5px; cursor: pointer;">
            🖨 Распечатать план на неделю
        </button>
    """, height=50)

# ОСНОВНОЙ ИНТЕРФЕЙС
tab1, tab2 = st.tabs(["📊 Real-time Terminal", "📅 Weekly Strategy"])

with tab1:
    placeholder = st.empty()
    # Здесь остается твой живой код из v4.6...

with tab2:
    st.subheader("Weekly Strategy Planner")
    st.write("Сгенерированная форма для печати и анализа с Юлей.")
    
    weekly_df = get_weekly_plan()
    st.table(weekly_df)
    
    print_page()

# СТИЛИЗАЦИЯ ДЛЯ ПЕЧАТИ
st.markdown("""
    <style>
    @media print {
        .stButton, .stTabs, header, footer { display: none !important; }
        .main { visibility: visible !important; }
    }
    </style>
""", unsafe_allow_html=True)
