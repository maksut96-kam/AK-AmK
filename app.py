import streamlit as st
from skyfield.api import load, Topos
from datetime import datetime, timedelta
import pandas as pd
import streamlit.components.v1 as components
import math
import os
import base64

# 1. Системные настройки
st.set_page_config(page_title="Julia Assistant Astro Coordination Center", layout="wide")

@st.cache_resource
def init_engine():
    ts = load.timescale()
    eph = load('de421.bsp')
    return ts, eph

ts, eph = init_engine()

# --- Константы ---
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]
NAK_LORDS = ["Кету", "Венера", "Солнце", "Луна", "Марс", "Раху", "Юпитер", "Сатурн", "Меркурий"] * 3
P_ICONS = {'Sun': '☀️ Sun', 'Moon': '🌙 Moon', 'Mars': '🔴 Mars', 'Mercury': '☿️ Merc', 'Jupiter': '🔵 Jup', 'Venus': '♀️ Venus', 'Saturn': '🪐 Sat', 'Rahu': '🐲 Rahu', 'Ketu': '🐍 Ketu'}
Z_ICONS = {s: f"| {s}" for s in ZODIAC_SIGNS} # Упрощено для интеграции

def get_dynamic_ayanamsa(t):
    T = (t.tt - 2451545.0) / 36525.0
    return 23.856235 + (2.30142 * T) + (0.000139 * T**2)

def get_planet_data(t):
    current_ayan = get_dynamic_ayanamsa(t)
    earth = eph['earth']
    planets_objects = {
        'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 
        'Mercury': eph['mercury'], 'Jupiter': eph['jupiter_barycenter'], 
        'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']
    }
    
    res = []
    # Для определения ретроградности берем малый шаг dt
    t2 = ts.tt_jd(t.tt + 0.001) 
    
    for name, obj in planets_objects.items():
        pos1 = earth.at(t).observe(obj).ecliptic_latlon()
        pos2 = earth.at(t2).observe(obj).ecliptic_latlon()
        
        lon = (pos1[1].degrees - current_ayan) % 360
        is_retro = pos2[1].degrees < pos1[1].degrees
        
        # Логика АК для ретроградных планет: 30 - градус
        deg_in_sign = lon % 30
        effective_deg = (30 - deg_in_sign) if (is_retro and name != 'Sun' and name != 'Moon') else deg_in_sign
        
        res.append({'Planet': name, 'Lon': lon, 'Deg': deg_in_sign, 'EffDeg': effective_deg, 'Retro': is_retro})
    
    df_ak = pd.DataFrame(res).sort_values(by='EffDeg', ascending=False).reset_index(drop=True)
    roles = ['AK', 'AmK', 'BK', 'MK', 'PiK', 'PK', 'GK']
    df_ak['Role'] = roles[:len(df_ak)]
    
    # Узлы (Mean Nodes)
    T = (t.tt - 2451545.0) / 36525.0
    node_mean_lon = (125.0445550 - 1934.1361849 * T + 0.0020762 * T**2) % 360
    ra_lon = (node_mean_lon - current_ayan) % 360
    df_nodes = pd.DataFrame([
        {'Planet': 'Rahu', 'Lon': ra_lon, 'Deg': ra_lon % 30, 'Role': '-', 'Retro': True},
        {'Planet': 'Ketu', 'Lon': (ra_lon + 180) % 360, 'Deg': (ra_lon + 180) % 30, 'Role': '-', 'Retro': True}
    ])
    
    return pd.concat([df_ak, df_nodes], ignore_index=True), current_ayan

def get_lunar_details(t):
    earth, sun, moon = eph['earth'], eph['sun'], eph['moon']
    s_lon = earth.at(t).observe(sun).ecliptic_latlon()[1].degrees
    m_lon = earth.at(t).observe(moon).ecliptic_latlon()[1].degrees
    diff = (m_lon - s_lon) % 360
    tithi = math.ceil(diff / 12) or 1
    
    # Moon Visualizer (8 фаз)
    icons = ["🌑","🌒","🌓","🌔","🌕","🌖","🌗","🌘"]
    icon = icons[int(((diff + 22.5) % 360) / 45)]
    
    # Расчет до Сизигия
    target_diff = 180 if diff < 180 else 360
    hours_to_go = (target_diff - diff) / 0.508 # средняя скорость Луны ~0.508 град/час
    
    return tithi, icon, diff, hours_to_go

def get_full_info(row):
    nak_idx = int(row['Lon'] / (360/27)) % 27
    sign = ZODIAC_SIGNS[int(row['Lon'] / 30)]
    retro_mark = " (R)" if row.get('Retro') else ""
    return f"{P_ICONS.get(row['Planet'], row['Planet'])}{retro_mark} | {sign} | ☸️ {NAKSHATRAS[nak_idx]}"

# --- ИНТЕРФЕЙС ---
st.markdown('<h1 style="text-align:center;">Julia Assistant Astro Coordination Center</h1>', unsafe_allow_html=True)

now_utc = datetime.utcnow()
t_now = ts.utc(now_utc.year, now_utc.month, now_utc.day, now_utc.hour, now_utc.minute, now_utc.second)
df, _ = get_planet_data(t_now)
tithi, l_icon, l_diff, h_to_siz = get_lunar_details(t_now)

# Блок "Совет Хозяина"
advice_map = {
    1: "Начинайте новые проекты, энергия обновления.",
    4: "День пустых рук (Рикта). Не начинайте важных дел.",
    9: "Энергия преодоления препятствий. Будьте настойчивы.",
    11: "Экадаши. Благоприятно для очищения и поста.",
    15: "Полнолуние. Максимум эмоций, будьте осторожны в суждениях."
}
current_advice = advice_map.get(tithi, "Обычный рабочий день, следуйте своему плану.")

c_m1, c_m2, c_m3 = st.columns(3)
with c_m1:
    st.metric("🌙 Лунная Фаза", f"{l_icon} {tithi} Титхи")
with c_m2:
    td = timedelta(hours=h_to_siz)
    st.metric("⏳ До Полнолуния/Новолуния", f"{td.days}д {td.seconds//3600}ч")
with c_m3:
    st.info(f"💡 **Совет Хозяина:** {current_advice}")

tab1, tab2 = st.tabs(["📊 Прямой эфир", "📅 Высокоточный Таймлайн"])

with tab1:
    st.table(df[['Role', 'Planet', 'Deg', 'Retro']])
    st.metric("💎 АК (Атма-карака)", get_full_info(df.iloc[0]))
    st.metric("🥈 AmK (Аматья-карака)", get_full_info(df.iloc[1]))

with tab2:
    st.subheader("📅 Оптимизированный планировщик")
    # (Здесь остаются инпуты дат из вашего кода)
    if st.button('🚀 Рассчитать периоды'):
        # Оптимизированный поиск
        curr = datetime.combine(st.session_state.s_dt.date(), st.session_state.s_dt.time()) - timedelta(hours=3)
        end = datetime.combine(st.session_state.e_dt.date(), st.session_state.e_dt.time()) - timedelta(hours=3)
        events = []
        
        last_pair = None
        while curr < end:
            t_check = ts.utc(curr.year, curr.month, curr.day, curr.hour, curr.minute)
            df_check, _ = get_planet_data(t_check)
            current_pair = f"{df_check.iloc[0]['Planet']}-{df_check.iloc[1]['Planet']}"
            
            if last_pair and current_pair != last_pair:
                # Уточнение минуты (бисекция/линейный откат)
                for m in range(60):
                    precise_t = curr - timedelta(minutes=60-m)
                    t_p = ts.utc(precise_t.year, precise_t.month, precise_t.day, precise_t.hour, precise_t.minute)
                    df_p, _ = get_planet_data(t_p)
                    if f"{df_p.iloc[0]['Planet']}-{df_p.iloc[1]['Planet']}" == current_pair:
                        events.append({
                            "Время (Сочи)": (precise_t + timedelta(hours=3)).strftime("%d.%m %H:%M"),
                            "АК": get_full_info(df_p.iloc[0]),
                            "AmK": get_full_info(df_p.iloc[1])
                        })
                        break
            
            last_pair = current_pair
            curr += timedelta(hours=1) # Шаг 1 час для скорости
            
        st.table(pd.DataFrame(events))
