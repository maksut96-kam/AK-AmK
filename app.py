import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components

# 1. Настройки
st.set_page_config(page_title="Max Pro-Trader CC", layout="wide")

st.markdown("""
    <style>
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: #f0f2f6; border-radius: 5px; }
    .stTabs [aria-selected="true"] { background-color: #4CAF50 !important; color: white !important; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>Max Pro-Trader Coordination center</h1>", unsafe_allow_html=True)

# Живое обновление каждую секунду
st_autorefresh(interval=1000, key="realtime_tick")

# Константы
LAHIRI_AYANAMSA = 24.2255
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]

@st.cache_resource
def init_engine():
    return load.timescale(), load('de421.bsp')

ts, eph = init_engine()

def check_gandanta(lon):
    threshold = 3.333
    for junction in [0, 120, 240, 360]:
        if abs(lon - junction) <= threshold or abs(lon - (junction + 360) % 360) <= threshold:
            return True
    return False

def get_planet_data(t):
    planets = {'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 'Mercury': eph['mercury'], 
               'Jupiter': eph['jupiter_barycenter'], 'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']}
    res = []
    for name, obj in planets.items():
        lon = (eph['earth'].at(t).observe(obj).ecliptic_latlon()[1].degrees - LAHIRI_AYANAMSA) % 360
        res.append({'Planet': name, 'Lon': lon, 'Deg': round(lon % 30, 4), 'IsGandanta': check_gandanta(lon)})
    
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    df.index += 1
    roles = ['AK', 'AmK', 'BK', 'MK', 'PK', 'GK', 'DK']
    df['Role'] = [f"{roles[i]} ⚠️ Узел" if df.iloc[i]['IsGandanta'] else roles[i] for i in range(len(roles))]
    df['Сила'] = df['Deg'].apply(lambda d: "💪 Высокая" if 10 <= d <= 20 else "⚡ Средняя")
    return df

def format_info(row):
    nak = NAKSHATRAS[int(row['Lon'] / (360/27)) % 27]
    sign = ZODIAC_SIGNS[int(row['Lon'] / 30)]
    prefix = "⚠️ Узел! " if row.get('IsGandanta') else ""
    return f"{prefix}{row['Planet']} ({sign}, {nak})"

# Кешируем поиск ротации, чтобы не искать каждую секунду (обновляем раз в 5 минут)
@st.cache_data(ttl=300)
def find_next_rotation(now_dt):
    t_c = ts.utc(now_dt.year, now_dt.month, now_dt.day, now_dt.hour-3, now_dt.minute)
    df = get_planet_data(t_c)
    ak_now, amk_now = df.iloc[0]['Planet'], df.iloc[1]['Planet']
    
    for m in range(1, 1440):
        t_f = ts.utc(now_dt.year, now_dt.month, now_dt.day, now_dt.hour-3, now_dt.minute + m)
        df_f = get_planet_data(t_f)
        if df_f.iloc[0]['Planet'] != ak_now or df_f.iloc[1]['Planet'] != amk_now:
            return {
                "mins": m,
                "time": (now_dt + timedelta(minutes=m)).strftime("%H:%M"),
                "ak": df_f.iloc[0],
                "amk": df_f.iloc[1]
            }
    return None

@st.cache_data(ttl=3600)
def build_weekly_plan():
    now_ref = datetime.utcnow() + timedelta(hours=3)
    start_mon = now_ref - timedelta(days=now_ref.weekday())
    start_mon = start_mon.replace(hour=2, minute=0, second=0, microsecond=0)
    events, last_pair = [], ""
    for h in range(0, 130):
        base_time = start_mon + timedelta(hours=h)
        t_w = ts.utc(base_time.year, base_time.month, base_time.day, base_time.hour-3, 0)
        df_w = get_planet_data(t_w)
        pair_key = f"{df_w.iloc[0]['Planet']}-{df_w.iloc[1]['Planet']}"
        if pair_key != last_pair:
            events.append({
                "Дата/Время": base_time.strftime("%d.%m %H:%M"),
                "Пара AK / AmK": f"AK: {format_info(df_w.iloc[0])} | AmK: {format_info(df_w.iloc[1])}",
                "Статус": "⚠️ Ганданта!" if (df_w.iloc[0]['IsGandanta'] or df_w.iloc[1]['IsGandanta']) else "✅"
            })
            last_pair = pair_key
    return pd.DataFrame(events)

tab1, tab2 = st.tabs(["📊 Прямой эфир", "📅 План для Юли"])

with tab1:
    now = datetime.utcnow() + timedelta(hours=3)
    t_c = ts.utc(now.year, now.month, now.day, now.hour-3, now.minute, now.second)
    df_current = get_planet_data(t_c)
    
    st.write(f"### 🕒 Сочи: **{now.strftime('%H:%M:%S')}**")
    st.table(df_current[['Role', 'Planet', 'Deg', 'Сила']])
    
    st.markdown("---")
    st.subheader("🚀 Ближайшая ротация")
    
    # Берем данные ротации из кеша (обновляются раз в 5 минут, а не каждую секунду)
    rotation = find_next_rotation(now.replace(second=0, microsecond=0))
    if rotation:
        st.success(f"📅 Смена через {rotation['mins']} мин: **{rotation['time']}**")
        c1, c2 = st.columns(2)
        with c1: st.info(f"🔵 **Новая АК:**\n\n{format_info(rotation['ak'])}")
        with c2: st.warning(f"🟡 **Новая АмК:**\n\n{format_info(rotation['amk'])}")

with tab2:
    st.subheader("Стратегический таймлайн")
    yulia_data = build_weekly_plan()
    st.table(yulia_data)
    components.html("<script>function pr(){window.print();}</script><button onclick='pr()' style='width:100%; height:45px; background:#4CAF50; color:white; border:none; border-radius:10px; cursor:pointer;'>🖨 ПЕЧАТЬ</button>", height=60)
