import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd
import time
import streamlit.components.v1 as components

# 1. Настройка и заголовок
st.set_page_config(page_title="Max Pro-Trader CC", layout="wide")
st.markdown("<h1 style='text-align: center;'>Max Pro-Trader Coordination center</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>v5.3 Command & Strategy | XAU/USD | Sochi (UTC+3)</p>", unsafe_allow_html=True)

# Константы
LAHIRI_AYANAMSA = 24.2255
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]

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

def get_info_string(row):
    nak = NAKSHATRAS[int(row['Lon'] / (360/27)) % 27]
    sign = ZODIAC_SIGNS[int(row['Lon'] / 30)]
    return f"{row['Planet']} ({sign}, {nak})"

# --- Инициализация эфемерид ---
ts = load.timescale()
eph = load('de421.bsp')

tab1, tab2 = st.tabs(["📊 Главный терминал", "📅 Координация с Юлей"])

with tab2:
    st.subheader("План движения и взаимодействия планет на неделю")
    
    # Расчет с ближайшего понедельника 02:00
    now = datetime.utcnow() + timedelta(hours=3)
    start_monday = now - timedelta(days=now.weekday())
    start_monday = start_monday.replace(hour=2, minute=0, second=0, microsecond=0)
    
    weekly_events = []
    # Сканируем неделю с шагом в 4 часа для поиска моментов смены AK/AmK
    for hour in range(0, 120, 4): # 5 дней по 24 часа
        check_time = start_monday + timedelta(hours=hour)
        if check_time.weekday() > 4: continue # Только до пятницы
        
        t = ts.utc(check_time.year, check_time.month, check_time.day, check_time.hour - 3, check_time.minute)
        df_w = get_planet_data(t, eph)
        ak, amk = df_w.iloc[0], df_w.iloc[1]
        
        weekly_events.append({
            "Дата и время": check_time.strftime("%d.%m %H:%M"),
            "Пара (AK / AmK)": f"AK: {get_info_string(ak)} | AmK: {get_info_string(amk)}",
            "Прогноз Max/Юля": "__________________________"
        })
    
    event_df = pd.DataFrame(weekly_events)
    st.table(event_df)
    
    components.html("""
        <script>function printPage() { window.print(); }</script>
        <button onclick="printPage()" style="width:100%; height:45px; background:#4CAF50; color:white; border:none; border-radius:8px; cursor:pointer; font-weight:bold;">
            🖨 РАСПЕЧАТАТЬ ПЛАН НА НЕДЕЛЮ
        </button>
    """, height=60)

with tab1:
    placeholder = st.empty()
    while True:
        curr_now = datetime.utcnow() + timedelta(hours=3)
        t_curr = ts.utc(curr_now.year, curr_now.month, curr_now.day, curr_now.hour - 3, curr_now.minute, curr_now.second)
        df = get_planet_data(t_curr, eph)
        
        # Поиск следующей смены (через 1 час для примера в табло)
        t_next = ts.utc(curr_now.year, curr_now.month, curr_now.day, curr_now.hour - 2, curr_now.minute)
        df_next = get_planet_data(t_next, eph)
        
        with placeholder.container():
            st.write(f"### 🕒 Время Сочи: {curr_now.strftime('%H:%M:%S')}")
            
            # Основная таблица
            df_v = df.copy()
            df_v['Знак'] = df_v['Lon'].apply(lambda x: ZODIAC_SIGNS[int(x/30)])
            df_v['Накшатра'] = df_v['Lon'].apply(lambda x: NAKSHATRAS[int(x/(360/27)) % 27])
            df_v['Роль'] = ['AK', 'AmK', 'BK', 'MK', 'PK', 'GK', 'DK']
            st.table(df_v[['Role', 'Planet', 'Знак', 'Накшатра', 'Deg']])
            
            # ИНФОРМАЦИОННОЕ ТАБЛО
            st.markdown("---")
            st.subheader("📢 Опережающий анализ (Next Shift)")
            c1, c2 = st.columns(2)
            with c1:
                st.info(f"**Следующая AK:** {get_info_string(df_next.iloc[0])}")
            with c2:
                st.warning(f"**Следующая AmK:** {get_info_string(df_next.iloc[1])}")
            st.write(f"*Ожидаемое время ротации: {(curr_now + timedelta(hours=1)).strftime('%H:%M')}*")

        time.sleep(1)
