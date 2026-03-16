import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd
from streamlit_autorefresh import st_autorefresh
import streamlit.components.v1 as components

# 1. Настройки
st.set_page_config(page_title="Max Pro-Trader CC", layout="wide")

# Движок расчетов
@st.cache_resource
def init_engine():
    return load.timescale(), load('de421.bsp')

ts, eph = init_engine()
LAHIRI_AYANAMSA = 24.2255
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]

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
    return f"{row['Planet']} ({sign}, {nak})"

# --- МЕНЮ В САЙДБАРЕ ---
st.sidebar.title("Навигация")
page = st.sidebar.radio("Выберите режим:", ["📊 Прямой эфир", "📅 План для Юли"])

# --- СТРАНИЦА 1: ПРЯМОЙ ЭФИР ---
if page == "📊 Прямой эфир":
    st_autorefresh(interval=1000, key="live_tick")
    st.header("📊 Прямой эфир (Real-time)")
    
    now = datetime.utcnow() + timedelta(hours=3)
    t_now = ts.utc(now.year, now.month, now.day, now.hour-3, now.minute, now.second)
    df_current = get_planet_data(t_now)
    
    st.subheader(f"🕒 Время Сочи: {now.strftime('%H:%M:%S')}")
    st.table(df_current[['Role', 'Planet', 'Deg', 'Сила']])
    
    st.markdown("---")
    st.subheader("🚀 Ближайшая ротация (смена пары)")
    
    ak_now, amk_now = df_current.iloc[0]['Planet'], df_current.iloc[1]['Planet']
    for m in range(1, 1440, 1):
        t_f = ts.utc(now.year, now.month, now.day, now.hour-3, now.minute + m)
        df_f = get_planet_data(t_f)
        if df_f.iloc[0]['Planet'] != ak_now or df_f.iloc[1]['Planet'] != amk_now:
            st.success(f"📅 Смена через {m} мин: **{(now + timedelta(minutes=m)).strftime('%H:%M')}**")
            c1, c2 = st.columns(2)
            with c1: st.info(f"🔵 **Новая АК:**\n\n{format_info(df_f.iloc[0])}")
            with c2: st.warning(f"🟡 **Новая АмК:**\n\n{format_info(df_f.iloc[1])}")
            break

# --- СТРАНИЦА 2: ПЛАН ДЛЯ ЮЛИ ---
elif page == "📅 План для Юли":
    st.header("📅 Стратегический план (Юля)")
    st.info("Этот раздел рассчитывается один раз. Чтобы обновить данные, просто перезагрузите страницу.")
    
    @st.cache_data(ttl=86400) # Кеш на 24 часа
    def generate_yulia_plan():
        now_ref = datetime.utcnow() + timedelta(hours=3)
        start_mon = now_ref - timedelta(days=now_ref.weekday())
        start_mon = start_mon.replace(hour=2, minute=0, second=0)
        events, last_pair = [], ""
        for h in range(0, 125):
            base_time = start_mon + timedelta(hours=h)
            t_w = ts.utc(base_time.year, base_time.month, base_time.day, base_time.hour-3, 0)
            df_w = get_planet_data(t_w)
            pair_key = f"{df_w.iloc[0]['Planet']}-{df_w.iloc[1]['Planet']}"
            if pair_key != last_pair:
                events.append({
                    "Дата/Время": base_time.strftime("%d.%m %H:%M"),
                    "Пара AK / AmK": f"AK: {format_info(df_w.iloc[0])} | AmK: {format_info(df_w.iloc[1])}",
                    "Статус": "⚠️ Ганданта!" if (df_w.iloc[0]['IsGandanta'] or df_w.iloc[1]['IsGandanta']) else "✅ Норма"
                })
                last_pair = pair_key
        return pd.DataFrame(events)

    with st.spinner("Генерация плана на неделю..."):
        df_yulia = generate_yulia_plan()
        st.table(df_yulia)
    
    components.html("<script>function pr(){window.print();}</script><button onclick='pr()' style='width:100%; height:45px; background:#4CAF50; color:white; border:none; border-radius:10px; cursor:pointer;'>🖨 ПЕЧАТЬ ПЛАНА</button>", height=60)
