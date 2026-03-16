import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd
import time
import streamlit.components.v1 as components

# 1. Настройка интерфейса
st.set_page_config(page_title="Max Pro-Trader CC", layout="wide")
st.markdown("<h1 style='text-align: center;'>Max Pro-Trader Coordination center</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>v5.5 Stable Build | XAU/USD | Сочи (UTC+3)</p>", unsafe_allow_html=True)

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
    return df

def format_planet_info(row):
    nak = NAKSHATRAS[int(row['Lon'] / (360/27)) % 27]
    sign = ZODIAC_SIGNS[int(row['Lon'] / 30)]
    return f"{row['Planet']} ({sign}, {nak})"

# Загрузка эфемерид
ts = load.timescale()
eph = load('de421.bsp')

tab1, tab2 = st.tabs(["📊 Главный терминал", "📅 Координация с Юлей"])

with tab2:
    st.subheader("План стратегического взаимодействия (Пн-Пт)")
    # Расчет с понедельника 02:00
    now_ref = datetime.utcnow() + timedelta(hours=3)
    start_monday = now_ref - timedelta(days=now_ref.weekday())
    start_monday = start_monday.replace(hour=2, minute=0, second=0, microsecond=0)
    
    weekly_schedule = []
    last_p = ""
    # Сканирование недели с шагом 1 час для поиска точек пересечения
    for h in range(0, 120): 
        check_t = start_monday + timedelta(hours=h)
        if check_t.weekday() > 4: break
        
        t_w = ts.utc(check_t.year, check_t.month, check_t.day, check_t.hour-3, check_t.minute)
        df_w = get_planet_data(t_w, eph)
        ak_w, amk_w = df_w.iloc[0], df_w.iloc[1]
        
        curr_p = f"{ak_w['Planet']}-{amk_w['Planet']}"
        if curr_p != last_p:
            weekly_schedule.append({
                "Дата и время": check_t.strftime("%d.%m %H:%M"),
                "Пара (AK / AmK)": f"AK: {format_planet_info(ak_w)}\nAmK: {format_planet_info(amk_w)}",
                "Прогноз Max/Юля": "__________________________"
            })
            last_p = curr_p

    st.table(pd.DataFrame(weekly_schedule))
    components.html("<script>function pr(){window.print();}</script><button onclick='pr()' style='width:100%; height:45px; background:#4CAF50; color:white; border:none; border-radius:10px; cursor:pointer;'>🖨 ПЕЧАТЬ ПЛАНА</button>", height=60)

with tab1:
    placeholder = st.empty()
    while True:
        c_now = datetime.utcnow() + timedelta(hours=3)
        t_c = ts.utc(c_now.year, c_now.month, c_now.day, c_now.hour-3, c_now.minute, c_now.second)
        df_now = get_planet_data(t_c, eph)
        
        # ДЕТЕКТОР БУДУЩЕЙ СМЕНЫ
        future_shift = None
        for i in range(1, 1440, 10): # Ищем в ближайшие 24 часа с шагом 10 мин
            t_f = ts.utc(c_now.year, c_now.month, c_now.day, c_now.hour-3, c_now.minute + i)
            df_f = get_planet_data(t_f, eph)
            if df_f.iloc[0]['Planet'] != df_now.iloc[0]['Planet'] or df_f.iloc[1]['Planet'] != df_now.iloc[1]['Planet']:
                future_shift = (c_now + timedelta(minutes=i), df_f.iloc[0], df_f.iloc[1])
                break

        with placeholder.container():
            st.write(f"### 🕒 Сочи: {c_now.strftime('%H:%M:%S')}")
            
            # Основная таблица
            df_v = df_now.copy()
            df_v['Знак'] = df_v['Lon'].apply(lambda x: ZODIAC_SIGNS[int(x/30)])
            df_v['Накшатра'] = df_v['Lon'].apply(lambda x: NAKSHATRAS[int(x/(360/27)) % 27])
            st.table(df_v[['Role', 'Planet', 'Знак', 'Накшатра', 'Deg']])
            
            # ТАБЛО БУДУЩИХ ПЕРЕМЕН
            st.markdown("---")
            st.subheader("📢 Анонс следующей ротации")
            if future_shift:
                time_f, ak_f, amk_f = future_shift
                c1, c2 = st.columns(2)
                c1.info(f"**Будущая AK:**\n{format_planet_info(ak_f)}")
                c2.warning(f"**Будущая AmK:**\n{format_planet_info(amk_f)}")
                st.write(f"**Ориентировочное время смены:** {time_f.strftime('%d.%m %H:%M')}")
            else:
                st.write("В ближайшие 24 часа смены ролей не обнаружено.")
            
        time.sleep(1)
