import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components

# 1. Системные настройки
st.set_page_config(page_title="Max Pro-Trader CC", layout="wide")

# Автообновление экрана (раз в 2 секунды, чтобы не перегружать)
st_autorefresh(interval=2000, key="stable_refresh")

# Константы
LAHIRI_AYANAMSA = 24.2255
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]

# Движок (Кешируем один раз)
@st.cache_resource
def init_engine():
    return load.timescale(), load('de421.bsp')

ts, eph = init_engine()

def get_planet_data(t):
    planets = {'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 'Mercury': eph['mercury'], 
               'Jupiter': eph['jupiter_barycenter'], 'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']}
    res = []
    for name, obj in planets.items():
        lon = (eph['earth'].at(t).observe(obj).ecliptic_latlon()[1].degrees - LAHIRI_AYANAMSA) % 360
        res.append({'Planet': name, 'Lon': lon, 'Deg': round(lon % 30, 4)})
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    df.index += 1
    df['Role'] = ['AK', 'AmK', 'BK', 'MK', 'PK', 'GK', 'DK']
    return df

def get_info(row):
    nak = NAKSHATRAS[int(row['Lon'] / (360/27)) % 27]
    sign = ZODIAC_SIGNS[int(row['Lon'] / 30)]
    return f"{row['Planet']} ({sign}, {nak})"

# --- ИНТЕРФЕЙС ---
st.markdown("<h1 style='text-align: center;'>Max Pro-Trader Coordination center</h1>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📊 Прямой эфир", "📅 План для Юли"])

with tab1:
    now = datetime.utcnow() + timedelta(hours=3)
    t_c = ts.utc(now.year, now.month, now.day, now.hour-3, now.minute, now.second)
    df = get_planet_data(t_c)
    ak, amk = df.iloc[0], df.iloc[1]
    
    st.write(f"### 🕒 Сочи: {now.strftime('%H:%M:%S')}")
    
    # Таблица планет
    df_v = df.copy()
    df_v['Знак'] = df_v['Lon'].apply(lambda x: ZODIAC_SIGNS[int(x/30)])
    df_v['Накшатра'] = df_v['Lon'].apply(lambda x: NAKSHATRAS[int(x/(360/27)) % 27])
    st.table(df_v[['Role', 'Planet', 'Знак', 'Накшатра', 'Deg']])
    
    # Ближайшая смена (быстрый расчет на 12 часов вперед)
    st.markdown("---")
    st.subheader("🚀 Ближайшая смена Карака")
    ak_now, amk_now = df.iloc[0]['Planet'], df.iloc[1]['Planet']
    found = False
    for m in range(1, 720, 5): # Шаг 5 мин для скорости
        t_f = ts.utc(now.year, now.month, now.day, now.hour-3, now.minute + m)
        df_f = get_planet_data(t_f)
        if df_f.iloc[0]['Planet'] != ak_now or df_f.iloc[1]['Planet'] != amk_now:
            st.success(f"📅 Смена через {m} мин: **{(now + timedelta(minutes=m)).strftime('%H:%M')}**")
            st.write(f"**Новая пара:** AK: {get_info(df_f.iloc[0])} | AmK: {get_info(df_f.iloc[1])}")
            found = True
            break
    if not found: st.write("В ближайшие 12 часов смен не ожидается.")

with tab2:
    st.subheader("Таймлайн на неделю (Пн-Пт)")
    
    @st.cache_data(ttl=3600)
    def generate_weekly():
        now_ref = datetime.utcnow() + timedelta(hours=3)
        start_mon = now_ref - timedelta(days=now_ref.weekday())
        start_mon = start_mon.replace(hour=2, minute=0, second=0, microsecond=0)
        
        events, last_pair = [], ""
        for m in range(0, 7200, 30): # Шаг 30 мин для стабильности
            ct = start_mon + timedelta(minutes=m)
            if ct.weekday() > 4: break
            t_w = ts.utc(ct.year, ct.month, ct.day, ct.hour-3, ct.minute)
            df_w = get_planet_data(t_w)
            curr_pair = f"{df_w.iloc[0]['Planet']}/{df_w.iloc[1]['Planet']}"
            
            if curr_pair != last_pair:
                events.append({
                    "Начало": ct.strftime("%d.%m %H:%M"),
                    "Пара (AK / AmK)": f"AK: {get_info(df_w.iloc[0])} | AmK: {get_info(df_w.iloc[1])}"
                })
                last_pair = curr_pair
        return pd.DataFrame(events)

    st.table(generate_weekly())
    components.html("<script>function pr(){window.print();}</script><button onclick='pr()' style='width:100%; height:45px; background:#4CAF50; color:white; border:none; border-radius:10px; cursor:pointer;'>🖨 ПЕЧАТЬ</button>", height=60)
