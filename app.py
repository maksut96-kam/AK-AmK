import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components

# 1. Системные настройки
st.set_page_config(page_title="Max Pro-Trader CC", layout="wide")
st.markdown("<h1 style='text-align: center;'>Max Pro-Trader Coordination center</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>v5.9.6 Stable Full | XAU/USD | Сочи (UTC+3)</p>", unsafe_allow_html=True)

# Обновляем страницу каждые 10 секунд
st_autorefresh(interval=10000, key="datarefresh")

# Константы
LAHIRI_AYANAMSA = 24.2255
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]

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

@st.cache_data(ttl=3600)
def build_weekly_plan_fast():
    now_ref = datetime.utcnow() + timedelta(hours=3)
    start_mon = now_ref - timedelta(days=now_ref.weekday())
    start_mon = start_mon.replace(hour=2, minute=0, second=0, microsecond=0)
    events, last_pair = [], ""
    for h in range(0, 120):
        ct = start_mon + timedelta(hours=h)
        t_w = ts.utc(ct.year, ct.month, ct.day, ct.hour-3, ct.minute)
        df_w = get_planet_data(t_w)
        pair_key = f"{df_w.iloc[0]['Planet']}-{df_w.iloc[1]['Planet']}"
        if pair_key != last_pair:
            events.append({
                "Время": ct.strftime("%d.%m %H:%M"),
                "Пара AK / AmK": f"AK: {format_info(df_w.iloc[0])}\nAmK: {format_info(df_w.iloc[1])}",
                "Прогноз": "________________"
            })
            last_pair = pair_key
    return pd.DataFrame(events)

tab1, tab2 = st.tabs(["📊 Прямой эфир", "📅 План для Юли"])

with tab1:
    now = datetime.utcnow() + timedelta(hours=3)
    t_c = ts.utc(now.year, now.month, now.day, now.hour-3, now.minute, now.second)
    df = get_planet_data(t_c)
    
    st.write(f"### 🕒 Сочи: {now.strftime('%H:%M:%S')}")
    df_v = df.copy()
    df_v['Знак'] = df_v['Lon'].apply(lambda x: ZODIAC_SIGNS[int(x/30)])
    df_v['Накшатра'] = df_v['Lon'].apply(lambda x: NAKSHATRAS[int(x/(360/27)) % 27])
    st.table(df_v[['Role', 'Planet', 'Знак', 'Накшатра', 'Deg', 'Сила']])
    
    st.markdown("---")
    st.subheader("🚀 Ближайшая ротация")
    
    # Расширенный поиск следующей смены
    ak_now = df.iloc[0]['Planet']
    amk_now = df.iloc[1]['Planet']
    next_shift = None
    
    # Сканируем вперед на 48 часов с шагом 15 минут для точности
    for m in range(15, 2880, 15):
        t_f = ts.utc(now.year, now.month, now.day, now.hour-3, now.minute + m)
        df_f = get_planet_data(t_f)
        # Проверяем смену АК или АмК
        if df_f.iloc[0]['Planet'] != ak_now or df_f.iloc[1]['Planet'] != amk_now:
            next_shift = {
                "time": (now + timedelta(minutes=m)).strftime("%d.%m %H:%M"),
                "ak": df_f.iloc[0],
                "amk": df_f.iloc[1]
            }
            break
    
    if next_shift:
        st.success(f"📅 **Следующая смена:** {next_shift['time']}")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"🔵 **Новая АК:**\n\n{format_info(next_shift['ak'])}")
        with col2:
            st.warning(f"🟡 **Новая АмК:**\n\n{format_info(next_shift['amk'])}")
    else:
        st.write("Поиск ближайшей ротации...")

with tab2:
    st.subheader("Стратегический таймлайн")
    weekly_data = build_weekly_plan_fast()
    st.table(weekly_data)
    components.html("<script>function pr(){window.print();}</script><button onclick='pr()' style='width:100%; height:45px; background:#4CAF50; color:white; border:none; border-radius:10px; cursor:pointer;'>🖨 ПЕЧАТЬ</button>", height=60)
