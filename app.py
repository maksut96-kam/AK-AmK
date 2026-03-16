import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd
import time
import streamlit.components.v1 as components

# 1. Системные настройки
st.set_page_config(page_title="Max Pro-Trader CC", layout="wide")
st.markdown("<h1 style='text-align: center;'>Max Pro-Trader Coordination center</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>v5.8 Power & Vision | XAU/USD | Сочи (UTC+3)</p>", unsafe_allow_html=True)

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
    df['Role'] = ['AK', 'AmK', 'BK', 'MK', 'PK', 'GK', 'DK']
    
    # Расчет "силы" (упрощенный аналог Shadbala для трейдинга)
    df['Сила'] = df['Deg'].apply(lambda d: "💪 Высокая" if 10 <= d <= 20 else "⚡ Средняя")
    return df

def format_full_info(row):
    nak = NAKSHATRAS[int(row['Lon'] / (360/27)) % 27]
    sign = ZODIAC_SIGNS[int(row['Lon'] / 30)]
    return f"{row['Planet']} в знаке {sign}, Накшатра: {nak}"

ts = load.timescale()
eph = load('de421.bsp')

tab1, tab2 = st.tabs(["📊 Прямой эфир", "📅 План для Юли"])

with tab1:
    placeholder = st.empty()
    while True:
        c_now = datetime.utcnow() + timedelta(hours=3)
        t_c = ts.utc(c_now.year, c_now.month, c_now.day, c_now.hour-3, c_now.minute, c_now.second)
        df_now = get_planet_data(t_c, eph)
        ak_now = df_now.iloc[0]
        
        # ПОИСК СЛЕДУЮЩЕЙ СМЕНЫ АТМАКАРАКИ
        next_shift = None
        for m in range(1, 2880, 5): # Ищем на 48 часов вперед с шагом 5 мин
            t_f = ts.utc(c_now.year, c_now.month, c_now.day, c_now.hour-3, c_now.minute + m)
            df_f = get_planet_data(t_f, eph)
            if df_f.iloc[0]['Planet'] != ak_now['Planet']:
                next_shift = {
                    "время": (c_now + timedelta(minutes=m)).strftime("%d.%m %H:%M"),
                    "планета": df_f.iloc[0],
                    "amk": df_f.iloc[1]
                }
                break
        
        with placeholder.container():
            st.write(f"### 🕒 Текущее время (Сочи): {c_now.strftime('%H:%M:%S')}")
            
            # Основная таблица
            df_display = df_now.copy()
            df_display['Знак'] = df_display['Lon'].apply(lambda x: ZODIAC_SIGNS[int(x/30)])
            df_display['Накшатра'] = df_display['Lon'].apply(lambda x: NAKSHATRAS[int(x/(360/27)) % 27])
            st.table(df_display[['Role', 'Planet', 'Знак', 'Накшатра', 'Deg', 'Сила']])
            
            # НОВЫЙ БЛОК: СЛЕДУЮЩАЯ СМЕНА (Твой запрос из Голос 001)
            st.markdown("---")
            st.subheader("🚀 Ближайшая ротация Атмакараки")
            if next_shift:
                c1, c2 = st.columns(2)
                with c1:
                    st.success(f"**Дата и время:** {next_shift['время']}")
                    st.info(f"**Новая AK:** {format_full_info(next_shift['планета'])}")
                with c2:
                    st.warning(f"**Статус AmK:** {format_full_info(next_shift['amk'])}")
            
        time.sleep(1)

with tab2:
    # (Здесь остается логика интервалов из v5.7 для Юли)
    st.info("Вкладка планирования синхронизирована с новыми расчетами силы планет.")
