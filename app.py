import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components

# 1. СИСТЕМНЫЕ НАСТРОЙКИ (Один раз)
st.set_page_config(page_title="Max Pro-Trader CC", layout="wide")

# Автообновление (раз в 2 секунды) — это "сердце" приложения
st_autorefresh(interval=2000, key="v9_heartbeat")

# Константы
LAHIRI_AYANAMSA = 24.2255
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]

# 2. ДВИЖОК РАСЧЕТОВ
@st.cache_resource
def get_engine():
    ts = load.timescale()
    eph = load('de421.bsp')
    return ts, eph

ts, eph = get_engine()

def get_data(time_obj):
    planets = {'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 'Mercury': eph['mercury'], 
               'Jupiter': eph['jupiter_barycenter'], 'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']}
    res = []
    for name, obj in planets.items():
        # Расчет сидерической долготы
        astrometric = eph['earth'].at(time_obj).observe(obj)
        _, lon, _ = astrometric.ecliptic_latlon()
        lon_deg = (lon.degrees - LAHIRI_AYANAMSA) % 360
        res.append({'Planet': name, 'Lon': lon_deg, 'Deg': round(lon_deg % 30, 4)})
    
    # Сортировка по градусам внутри знака для определения АК...ДК
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    df['Role'] = ['AK', 'AmK', 'BK', 'MK', 'PK', 'GK', 'DK']
    return df

def get_label(row):
    sign = ZODIAC_SIGNS[int(row['Lon'] / 30)]
    nak = NAKSHATRAS[int(row['Lon'] / (360/27)) % 27]
    return f"{row['Planet']} ({sign}, {nak})"

# --- ИНТЕРФЕЙС ---
st.markdown("<h1 style='text-align:center;'>Max Pro-Trader CC</h1>", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📊 ПРЯМОЙ ЭФИР", "📅 ПЛАН ЮЛИ"])

with tab1:
    now = datetime.utcnow() + timedelta(hours=3) # Время Сочи
    t_now = ts.utc(now.year, now.month, now.day, now.hour-3, now.minute, now.second)
    
    df_live = get_data(t_now)
    
    st.write(f"### 🕒 Сочи (Live): **{now.strftime('%H:%M:%S')}**")
    
    # Основная таблица текущих позиций
    display_df = df_live.copy()
    display_df['Знак'] = display_df['Lon'].apply(lambda x: ZODIAC_SIGNS[int(x/30)])
    display_df['Градус'] = display_df['Deg'].apply(lambda x: f"{x:.4f}°")
    st.table(display_df[['Role', 'Planet', 'Знак', 'Градус']])
    
    st.markdown("---")
    
    # Расчет ближайшей смены (на 24 часа вперед)
    st.subheader("🚀 Следующая ротация")
    ak_now, amk_now = df_live.iloc[0]['Planet'], df_live.iloc[1]['Planet']
    
    found_rot = False
    for m in range(1, 1440, 5): # Шаг 5 мин для скорости
        check_t = ts.utc(now.year, now.month, now.day, now.hour-3, now.minute + m)
        df_check = get_data(check_t)
        if df_check.iloc[0]['Planet'] != ak_now or df_check.iloc[1]['Planet'] != amk_now:
            st.success(f"📅 Смена через {m} мин в **{(now + timedelta(minutes=m)).strftime('%H:%M')}**")
            st.write(f"**Новая пара:** АК: {get_label(df_check.iloc[0])} | AmK: {get_label(df_check.iloc[1])}")
            found_rot = True
            break
    if not found_rot: st.info("В ближайшие 24 часа смен не зафиксировано.")

with tab2:
    st.subheader("Таймлайн на торговую неделю (Пн-Пт)")
    
    @st.cache_data(ttl=3600)
    def calc_weekly():
        now_ref = datetime.utcnow() + timedelta(hours=3)
        # Находим начало текущего понедельника
        monday = now_ref - timedelta(days=now_ref.weekday())
        monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)
        
        week_events, last_p = [], ""
        for h in range(0, 120, 1): # 5 дней по 24 часа
            check_dt = monday + timedelta(hours=h)
            t_h = ts.utc(check_dt.year, check_dt.month, check_dt.day, check_dt.hour-3, 0)
            df_h = get_data(t_h)
            curr_p = f"{df_h.iloc[0]['Planet']}/{df_h.iloc[1]['Planet']}"
            
            if curr_p != last_p:
                week_events.append({
                    "Начало": check_dt.strftime("%d.%m %H:00"),
                    "Пара (AK / AmK)": f"AK: {get_label(df_h.iloc[0])} | AmK: {get_label(df_h.iloc[1])}"
                })
                last_p = curr_p
        return pd.DataFrame(week_events)

    st.table(calc_weekly())
    components.html("<script>function pr(){window.print();}</script><button onclick='pr()' style='width:100%; height:40px; background:#4CAF50; color:white; border:none; border-radius:5px; cursor:pointer;'>🖨 ПЕЧАТЬ ПЛАНА</button>", height=50)
