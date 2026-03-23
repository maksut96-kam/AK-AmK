import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd
import streamlit.components.v1 as components

# 1. Системные настройки
st.set_page_config(page_title="Max Pro-Trader CC", layout="wide")

@st.cache_resource
def init_engine():
    ts = load.timescale()
    eph = load('de421.bsp')
    return ts, eph

ts, eph = init_engine()

# Константы
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]

def get_dynamic_ayanamsa(t):
    """Вычисление динамической Айанамши Лахири"""
    T = (t.tt - 2451545.0) / 36525.0
    # Формула N.C. Lahiri
    ayan = 23.856235 + (2.30142 * T) + (0.000139 * T**2)
    return ayan

def format_deg_to_min(deg_float):
    """Преобразование десятичных градусов в Гр° Мин' Сек\""""
    d = int(deg_float)
    m = int((deg_float - d) * 60)
    s = round((((deg_float - d) * 60) - m) * 60, 1)
    return f"{d}° {m}' {s}\""

def get_planet_data(t):
    current_ayan = get_dynamic_ayanamsa(t)
    planets = {
        'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 
        'Mercury': eph['mercury'], 'Jupiter': eph['jupiter_barycenter'], 
        'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']
    }
    res = []
    for name, obj in planets.items():
        # Сидерическая долгота = Геоцентрическая долгота - Айанамша
        lon = (eph['earth'].at(t).observe(obj).ecliptic_latlon()[1].degrees - current_ayan) % 360
        res.append({'Planet': name, 'Lon': lon, 'Deg': round(lon % 30, 4)})
    
    # Определение ролей по градусам (от АК до DK)
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    df['Role'] = ['AK', 'AmK', 'BK', 'MK', 'PK', 'GK', 'DK']
    # Сдвигаем индекс, чтобы начинался с 1
    df.index = df.index + 1
    return df, current_ayan

def get_info(row):
    nak_idx = int(row['Lon'] / (360/27)) % 27
    nak = NAKSHATRAS[nak_idx]
    sign = ZODIAC_SIGNS[int(row['Lon'] / 30)]
    return f"{row['Planet']} ({sign}, {nak})"

# --- ИНТЕРФЕЙС ---
st.markdown("<h1 style='text-align: center;'>Max Pro-Trader Coordination Center</h1>", unsafe_allow_html=True)

# ЖИВОЕ ВРЕМЯ
components.html("""
    <div style="background:#f0f2f6; padding:15px; border-radius:10px; text-align:center; font-family:sans-serif;">
        <h2 id="clock" style="margin:0; color:#1f77b4;">Загрузка времени...</h2>
        <p style="margin:0; color:gray;">Сочи (UTC+3)</p>
    </div>
    <script>
        function updateClock() {
            let d = new Date();
            let utc = d.getTime() + (d.getTimezoneOffset() * 60000);
            let sochi = new Date(utc + (3600000 * 3));
            document.getElementById('clock').innerHTML = sochi.toLocaleTimeString();
        }
        setInterval(updateClock, 1000);
        updateClock();
    </script>
""", height=110)

tab1, tab2 = st.tabs(["📊 Прямой эфир", "📅 План для Юли"])

with tab1:
    if st.button('🔄 Обновить расчет планет'):
        st.cache_data.clear()

    now = datetime.utcnow()
    # Skyfield работает в UTC, корректируем время для расчета
    t_now = ts.utc(now.year, now.month, now.day, now.hour, now.minute, now.second)
    
    df, ayan_val = get_planet_data(t_now)
    
    # Вывод информационной строки об Айанамше
    st.info(f"ℹ️ **Текущая Айанамша Лахири (динамическая):** {format_deg_to_min(ayan_val)}")
    
    # Подготовка таблицы для отображения
    df_v = df.copy()
    df_v['Знак'] = df_v['Lon'].apply(lambda x: ZODIAC_SIGNS[int(x/30)])
    df_v['Накшатра'] = df_v['Lon'].apply(lambda x: NAKSHATRAS[int(x / (360/27)) % 27])
    df_v['Градус'] = df_v['Deg'].apply(lambda x: f"{x:.4f}°")
    
    # Выводим таблицу с порядковым номером с 1
    st.table(df_v[['Role', 'Planet', 'Знак', 'Накшатра', 'Градус']])
    
    st.markdown("---")
    st.subheader("🚀 Ближайшая ротация")
    ak_now, amk_now = df.iloc[0]['Planet'], df.iloc[1]['Planet']
    
    # Поиск смены ролей в ближайшие 24 часа
    for m in range(1, 1440, 5):
        future_time = now + timedelta(minutes=m)
        t_f = ts.utc(future_time.year, future_time.month, future_time.day, future_time.hour, future_time.minute)
        df_f, _ = get_planet_data(t_f)
        if df_f.iloc[0]['Planet'] != ak_now or df_f.iloc[1]['Planet'] != amk_now:
            st.success(f"📅 Смена через {m} мин: **{(future_time + timedelta(hours=3)).strftime('%H:%M')}**")
            st.info(f"АК: {get_info(df_f.iloc[0])} | AmK: {get_info(df_f.iloc[1])}")
            break

with tab2:
    st.header("Таймлайн на неделю")
    @st.cache_data(ttl=3600)
    def generate_plan():
        now_ref = datetime.utcnow() + timedelta(hours=3)
        monday = now_ref - timedelta(days=now_ref.weekday())
        monday = monday.replace(hour=0, minute=0, second=0)
        
        events, last_pair = [], ""
        for h in range(0, 120):
            ct = monday + timedelta(hours=h)
            # Переводим обратно в UTC для расчета
            t_w = ts.utc(ct.year, ct.month, ct.day, ct.hour-3, 0)
            df_w, _ = get_planet_data(t_w)
            curr_pair = f"{df_w.iloc[0]['Planet']}/{df_w.iloc[1]['Planet']}"
            if curr_pair != last_pair:
                events.append({
                    "Дата/Время": ct.strftime("%d.%m %H:00"),
                    "АК": get_info(df_w.iloc[0]),
                    "AmK": get_info(df_w.iloc[1])
                })
                last_pair = curr_pair
        return pd.DataFrame(events)

    df_plan = generate_plan()
    df_plan.index = df_plan.index + 1
    st.table(df_plan)
    components.html("<script>function pr(){window.print();}</script><button onclick='pr()' style='width:100%; height:45px; background:#4CAF50; color:white; border:none; border-radius:10px; cursor:pointer;'>🖨 ПЕЧАТЬ ПЛАНА</button>", height=60)
