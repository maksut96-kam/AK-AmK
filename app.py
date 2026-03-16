import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd
import time
import streamlit.components.v1 as components

# 1. Архитектурная настройка
st.set_page_config(page_title="Max Pro-Trader CC", layout="wide")
st.markdown("<h1 style='text-align: center;'>Max Pro-Trader Coordination center</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>v5.4 Owner Edition | XAU/USD | Сочи (UTC+3)</p>", unsafe_allow_html=True)

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
    # Сортировка по градусам для определения AK/AmK
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    df.index += 1
    df['Role'] = ['AK', 'AmK', 'BK', 'MK', 'PK', 'GK', 'DK']
    return df

def format_planet_info(row):
    nak = NAKSHATRAS[int(row['Lon'] / (360/27)) % 27]
    sign = ZODIAC_SIGNS[int(row['Lon'] / 30)]
    return f"{row['Planet']} в {nak} ({sign})"

# Загрузка движка
ts = load.timescale()
eph = load('de421.bsp')

tab1, tab2 = st.tabs(["📊 Главный терминал", "📅 Координация с Юлей"])

with tab2:
    st.subheader("План стратегического взаимодействия на неделю")
    # Расчет: Пн 02:00 -> Пт 23:45
    now = datetime.utcnow() + timedelta(hours=3)
    start_monday = now - timedelta(days=now.weekday())
    start_monday = start_monday.replace(hour=2, minute=0, second=0)
    
    weekly_schedule = []
    last_pair = ""
    
    # Сканирование недели с шагом 30 минут для поиска точек пересечения
    for m in range(0, 7200, 30): 
        check_time = start_monday + timedelta(minutes=m)
        if check_time.weekday() > 4: break # Стоп в конце пятницы
        
        t = ts.utc(check_time.year, check_time.month, check_time.day, check_time.hour-3, check_time.minute)
        df_w = get_planet_data(t, eph)
        ak, amk = df_w.iloc[0], df_w.iloc[1]
        
        current_pair = f"{ak['Planet']}-{amk['Planet']}"
        if current_pair != last_pair:
            weekly_schedule.append({
                "Дата и время заступления": check_time.strftime("%d.%m %H:%M"),
                "Пара (AK / AmK)": f"AK: {format_planet_info(ak)}\nAmK: {format_planet_info(amk)}",
                "Прогноз Max/Юля": "__________________________"
            })
            last_pair = current_pair

    st.table(pd.DataFrame(weekly_schedule))
    components.html("<script>function pr(){window.print();}</script><button onclick='pr()' style='width:100%; height:45px; background:#4CAF50; color:white; border:none; border-radius:10px; cursor:pointer;'>🖨 ПЕЧАТЬ ПЛАНА</button>", height=60)

with tab1:
    placeholder = st.empty()
    while True:
        c_now = datetime.utcnow() + timedelta(hours=3)
        t_c = ts.utc(c_now.year, c_now.month, c_now.day, c_now.hour-3, c_now.minute, c_now.second)
        df_now = get_planet_data(t_c, eph)
        
        # РАСЧЕТ БУДУЩЕЙ СМЕНЫ (настоящий прогноз, а не отписка)
        future_shift = None
        for i in range(1, 1440): # Ищем в пределах 24 часов
            t_f = ts.utc(c_now.year, c_now.month, c_now.day, c_now.hour-3, c_now.minute + i)
            df_f = get_planet_data(t_f, eph)
            if df_f.iloc[0]['Planet'] != df_now.iloc[0]['Planet'] or df_f.iloc[1]['Planet'] != df_now.iloc[1]['Planet']:
                future_shift = (c_now + timedelta(minutes=i), df_f.iloc[0], df_f.iloc[1])
                break

        with placeholder.container():
            st.write(f"### 🕒 Сочи: {c_now.strftime('%H:%M:%S')}")
            
            # Основная таблица текущего момента
            df_v = df_now.copy()
            df_v['Знак'] = df_v['Lon'].apply(lambda x: ZODIAC_SIGNS[int(x/30)])
            df_v['Накшатра'] = df_v['Lon'].apply(lambda x: NAKSHATRAS[int(x/(360/27)) % 27])
            st.table(df_v[['Role', 'Planet', 'Знак', 'Накшатра', 'Deg']])
            
            # ТАБЛО БУДУЩИХ ПЕРЕМЕН
            st.markdown("---")
            st.subheader("📢 Анонс следующих перемен (Детектор ротации)")
            if future_shift:
                time_f, ak_f, amk_f = future_shift
                c1, c2 = st.columns(2)
                with c1:
                    st.info(f"**Будущая AK:**\n{format_planet_info(ak_f)}")
                with col2 if 'col2' in locals() else c2:
                    st.warning(f"**Будущая AmK:**\n{format_planet_info(amk_f)}")
                st.write(f"**Ожидаемое время ротации:** {time_f.strftime('%d.%m %H:%M')}")
            else:
                st.write("В ближайшие 24 часа смены ролей не ожидается.")
            
        time.sleep(1)
