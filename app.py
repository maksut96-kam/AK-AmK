import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd
import time
import streamlit.components.v1 as components

# 1. Настройка и заголовок
st.set_page_config(page_title="Max Pro-Trader CC", layout="wide")
st.markdown("<h1 style='text-align: center;'>Max Pro-Trader Coordination center</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>v5.3.1 Stable | XAU/USD | Sochi (UTC+3)</p>", unsafe_allow_html=True)

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
    df['Role'] = ['AK', 'AmK', 'BK', 'MK', 'PK', 'GK', 'DK'] # Теперь роль создается ВНУТРИ функции
    return df

def get_info_str(row):
    nak = NAKSHATRAS[int(row['Lon'] / (360/27)) % 27]
    sign = ZODIAC_SIGNS[int(row['Lon'] / 30)]
    return f"{row['Planet']} в {nak} ({sign})"

# Инициализация
ts = load.timescale()
eph = load('de421.bsp')

tab1, tab2 = st.tabs(["📊 Главный терминал", "📅 Координация с Юлей"])

with tab2:
    st.subheader("План смен AK/AmK на неделю")
    now = datetime.utcnow() + timedelta(hours=3)
    # Понедельник 02:00
    start_monday = now - timedelta(days=now.weekday())
    start_monday = start_monday.replace(hour=2, minute=0, second=0, microsecond=0)
    
    weekly_rows = []
    # Проверка каждые 12 часов для выявления динамики (Пн-Пт)
    for hour in range(0, 120, 12):
        check_t = start_monday + timedelta(hours=hour)
        if check_t.weekday() > 4: continue
        
        t_w = ts.utc(check_t.year, check_t.month, check_t.day, check_t.hour - 3, check_t.minute)
        df_w = get_planet_data(t_w, eph)
        ak_w, amk_w = df_w.iloc[0], df_w.iloc[1]
        
        weekly_rows.append({
            "Дата и время": check_t.strftime("%d.%m %H:%M"),
            "Пара (AK / AmK)": f"AK: {get_info_str(ak_w)} | AmK: {get_info_str(amk_w)}",
            "Прогноз Max/Юля": "__________________________"
        })
    st.table(pd.DataFrame(weekly_rows))
    components.html("<script>function pr(){window.print();}</script><button onclick='pr()' style='width:100%; height:40px; background:#4CAF50; color:white; border:none; border-radius:8px; cursor:pointer;'>🖨 ПЕЧАТЬ ТАБЛИЦЫ</button>", height=50)

with tab1:
    placeholder = st.empty()
    while True:
        c_now = datetime.utcnow() + timedelta(hours=3)
        t_c = ts.utc(c_now.year, c_now.month, c_now.day, c_now.hour - 3, c_now.minute, c_now.second)
        df = get_planet_data(t_c, eph)
        ak, amk = df.iloc[0], df.iloc[1]
        
        with placeholder.container():
            st.write(f"### 🕒 Сочи: {c_now.strftime('%H:%M:%S')}")
            
            # РАБОЧАЯ ТАБЛИЦА (Исправлено)
            df_v = df.copy()
            df_v['Знак'] = df_v['Lon'].apply(lambda x: ZODIAC_SIGNS[int(x/30)])
            df_v['Накшатра'] = df_v['Lon'].apply(lambda x: NAKSHATRAS[int(x/(360/27)) % 27])
            st.table(df_v[['Role', 'Planet', 'Знак', 'Накшатра', 'Deg']])
            
            # АНОНС СЛЕДУЮЩИХ (Инфо-табло)
            st.markdown("---")
            st.subheader("📢 Анонс следующих перемен")
            # Смотрим на 24 часа вперед
            t_fut = ts.utc(c_now.year, c_now.month, c_now.day, c_now.hour + 21, c_now.minute)
            df_f = get_planet_data(t_fut, eph)
            
            col1, col2 = st.columns(2)
            with col1:
                st.info(f"**Будущая AK:** {get_info_str(df_f.iloc[0])}")
            with col2:
                st.warning(f"**Будущая AmK:** {get_info_str(df_f.iloc[1])}")
            st.write(f"*Ожидаемое состояние через 24 часа*")
            
        time.sleep(1)
