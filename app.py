import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd
import time
import streamlit.components.v1 as components

# 1. Настройки
st.set_page_config(page_title="Max Pro-Trader CC", layout="wide")
st.markdown("<h1 style='text-align: center;'>Max Pro-Trader Coordination center</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>v5.9.1 Stable | XAU/USD | Сочи (UTC+3)</p>", unsafe_allow_html=True)

# Константы
LAHIRI_AYANAMSA = 24.2255
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]

# Кешируем загрузку эфемерид для скорости
@st.cache_resource
def load_assets():
    return load.timescale(), load('de421.bsp')

ts, eph = load_assets()

def get_planet_data(t):
    planets = {'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 'Mercury': eph['mercury'], 
               'Jupiter': eph['jupiter_barycenter'], 'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']}
    res = []
    for name, obj in planets.items():
        lon = (eph['earth'].at(t).observe(obj).ecliptic_latlon()[1].degrees - LAHIRI_AYANAMSA) % 360
        res.append({'Planet': name, 'Lon': lon, 'Deg': lon % 30})
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    df.index += 1
    df['Role'] = ['AK', 'AmK', 'BK', 'MK', 'PK', 'GK', 'DK']
    df['Сила'] = df['Deg'].apply(lambda d: "💪 Высокая" if 10 <= d <= 20 else "⚡ Средняя")
    return df

def format_info(row):
    nak = NAKSHATRAS[int(row['Lon'] / (360/27)) % 27]
    sign = ZODIAC_SIGNS[int(row['Lon'] / 30)]
    return f"{row['Planet']} ({sign}, {nak})"

# --- ПРЕДВАРИТЕЛЬНЫЙ РАСЧЕТ ПЛАНА (чтобы вкладка не висела) ---
@st.cache_data(ttl=3600)
def generate_weekly_plan():
    now_ref = datetime.utcnow() + timedelta(hours=3)
    start_mon = now_ref - timedelta(days=now_ref.weekday())
    start_mon = start_mon.replace(hour=2, minute=0, second=0, microsecond=0)
    
    events, last_p = [], ""
    # Шаг 30 минут для баланса точности и скорости
    for m in range(0, 7200, 30):
        ct = start_mon + timedelta(minutes=m)
        if ct.weekday() > 4: break
        t_w = ts.utc(ct.year, ct.month, ct.day, ct.hour-3, ct.minute)
        df_w = get_planet_data(t_w)
        ak_w, amk_w = df_w.iloc[0], df_w.iloc[1]
        pair_id = f"{ak_w['Planet']}-{amk_w['Planet']}"
        if pair_id != last_p:
            events.append({
                "Время": ct.strftime("%d.%m %H:%M"), 
                "Пара AK / AmK": f"AK: {format_info(ak_w)}\nAmK: {format_info(amk_w)}", 
                "Прогноз": "________________"
            })
            last_p = pair_id
    return pd.DataFrame(events)

# Генерируем план заранее
weekly_df = generate_weekly_plan()

tab1, tab2 = st.tabs(["📊 Прямой эфир", "📅 План для Юли"])

with tab1:
    placeholder = st.empty()
    while True:
        now = datetime.utcnow() + timedelta(hours=3)
        t_c = ts.utc(now.year, now.month, now.day, now.hour-3, now.minute, now.second)
        df = get_planet_data(t_c)
        ak_now = df.iloc[0]
        
        # Поиск следующей смены (мини-скан на 24ч)
        next_shift = None
        for i in range(10, 1440, 20):
            t_f = ts.utc(now.year, now.month, now.day, now.hour-3, now.minute + i)
            df_f = get_planet_data(t_f)
            if df_f.iloc[0]['Planet'] != ak_now['Planet']:
                next_shift = {"time": (now + timedelta(minutes=i)).strftime("%d.%m %H:%M"), "ak": df_f.iloc[0], "amk": df_f.iloc[1]}
                break

        with placeholder.container():
            st.write(f"### 🕒 Сочи: {now.strftime('%H:%M:%S')}")
            df_v = df.copy()
            df_v['Знак'] = df_v['Lon'].apply(lambda x: ZODIAC_SIGNS[int(x/30)])
            df_v['Накшатра'] = df_v['Lon'].apply(lambda x: NAKSHATRAS[int(x/(360/27)) % 27])
            st.table(df_v[['Role', 'Planet', 'Знак', 'Накшатра', 'Deg', 'Сила']])
            
            st.markdown("---")
            st.subheader("🚀 Ближайшая ротация")
            if next_shift:
                # ВЕРТИКАЛЬНЫЕ БЛОКИ (Новая AK сверху, AmK снизу)
                st.info(f"**Смена в:** {next_shift['time']}")
                st.info(f"🔵 **Новая Атмакарака (AK):** {format_info(next_shift['ak'])}")
                st.warning(f"🟡 **Аматьякарака (AmK):** {format_info(next_shift['amk'])}")
            else:
                st.write("В ближайшие 24 часа смен не обнаружено.")
        time.sleep(1)

with tab2:
    st.subheader("Еженедельный план координации")
    if not weekly_df.empty:
        st.table(weekly_df)
        components.html("<script>function pr(){window.print();}</script><button onclick='pr()' style='width:100%; height:40px; background:#4CAF50; color:white; border:none; border-radius:10px; cursor:pointer;'>🖨 ПЕЧАТЬ ПЛАНА</button>", height=50)
    else:
        st.error("Ошибка загрузки данных плана. Попробуйте обновить страницу.")
