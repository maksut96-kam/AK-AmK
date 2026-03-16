import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components

# 1. Системные настройки
st.set_page_config(page_title="Max Pro-Trader CC", layout="wide")
st.markdown("<h1 style='text-align: center;'>Max Pro-Trader Coordination center</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>v5.7 Stable | XAU/USD | Сочи (UTC+3)</p>", unsafe_allow_html=True)

# Оптимальное обновление экрана (раз в секунду)
st_autorefresh(interval=1000, key="v57_refresh")

# Константы
LAHIRI_AYANAMSA = 24.2255
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]

# Кешируем загрузку планет, чтобы не тормозило
@st.cache_resource
def load_data():
    return load.timescale(), load('de421.bsp')

ts, eph = load_data()

def get_planet_data(t, eph):
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
tab1, tab2 = st.tabs(["📊 Прямой эфир", "📅 План для Юли (Интервалы)"])

with tab1:
    c_now = datetime.utcnow() + timedelta(hours=3)
    t_c = ts.utc(c_now.year, c_now.month, c_now.day, c_now.hour-3, c_now.minute, c_now.second)
    df = get_planet_data(t_c, eph)
    ak, amk = df.iloc[0], df.iloc[1]
    
    st.write(f"### 🕒 Сочи: {c_now.strftime('%H:%M:%S')}")
    
    # Основная таблица
    df_v = df.copy()
    df_v['Знак'] = df_v['Lon'].apply(lambda x: ZODIAC_SIGNS[int(x/30)])
    df_v['Накшатра'] = df_v['Lon'].apply(lambda x: NAKSHATRAS[int(x/(360/27)) % 27])
    st.table(df_v[['Role', 'Planet', 'Знак', 'Накшатра', 'Deg']])
    
    st.markdown("---")
    st.subheader("🎙 Голос Звезд: Анализ XAU/USD")
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Психология рынка (AK):** {get_info(ak)}\n\nНастроение на текущий цикл.")
    with col2:
        st.warning(f"**Инструментарий (AmK):** {get_info(amk)}\n\nМетод достижения целей.")

with tab2:
    st.subheader("Стратегический таймлайн на неделю")
    
    @st.cache_data(ttl=3600) # Кешируем план на час, чтобы не пересчитывать каждую секунду
    def get_weekly_plan():
        now_ref = datetime.utcnow() + timedelta(hours=3)
        start_monday = now_ref - timedelta(days=now_ref.weekday())
        start_monday = start_monday.replace(hour=2, minute=0, second=0, microsecond=0)
        
        events = []
        last_pair = ""
        last_time = start_monday
        
        # Поиск с точностью до 15 минут
        for m in range(0, 7200, 15):
            ct = start_monday + timedelta(minutes=m)
            if ct.weekday() > 4: break
            
            t_w = ts.utc(ct.year, ct.month, ct.day, ct.hour-3, ct.minute)
            df_w = get_planet_data(t_w, eph)
            ak_w, amk_w = df_w.iloc[0], df_w.iloc[1]
            
            curr_pair = f"{ak_w['Planet']}/{amk_w['Planet']}"
            if curr_pair != last_pair:
                if last_pair != "":
                    duration = ct - last_time
                    events[-1]["Длительность"] = f"{duration.seconds//3600}ч {(duration.seconds//60)%60}м"
                
                events.append({
                    "Начало": ct.strftime("%d.%m %H:%M"),
                    "Пара (AK / AmK)": f"AK: {get_info(ak_w)} \n AmK: {get_info(amk_w)}",
                    "Длительность": "...",
                    "Прогноз": "________________"
                })
                last_pair = curr_pair
                last_time = ct
        return pd.DataFrame(events)

    df_events = get_weekly_plan()
    st.table(df_events)
    components.html("<script>function pr(){window.print();}</script><button onclick='pr()' style='width:100%; height:45px; background:#4CAF50; color:white; border:none; border-radius:10px; cursor:pointer;'>🖨 ПЕЧАТЬ ТАЙМЛАЙНА</button>", height=60)
