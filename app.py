import streamlit as st
from skyfield.api import load
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

# --- Константы и Словари ---
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]
NAK_LORDS = ["Кету", "Венера", "Солнце", "Луна", "Марс", "Раху", "Юпитер", "Сатурн", "Меркурий"] * 3

P_ICONS = {'Sun': '☀️ Sun', 'Moon': '🌙 Moon', 'Mars': '🔴 Mars', 'Mercury': '☿️ Merc', 'Jupiter': '🔵 Jup', 'Venus': '♀️ Venus', 'Saturn': '🪐 Sat', 'Rahu': '🐲 Rahu', 'Ketu': '🐍 Ketu'}
Z_ICONS = {"Овен": "♈ Овен", "Телец": "♉ Телец", "Близнецы": "♊ Близн", "Рак": "♋ Рак", "Лев": "♌ Лев", "Дева": "♍ Дева", "Весы": "♎ Весы", "Скорпион": "♏ Скорп", "Стрелец": "♐ Стрел", "Козерог": "♑ Козег", "Водолей": "♒ Водол", "Рыбы": "♓ Рыбы"}

def get_dynamic_ayanamsa(t):
    T = (t.tt - 2451545.0) / 36525.0
    return 23.856235 + (2.30142 * T) + (0.000139 * T**2)

def get_planet_data(t):
    """ТВОЙ ОРИГИНАЛЬНЫЙ РАСЧЕТ + Улучшение: Ретроградность Парашары"""
    current_ayan = get_dynamic_ayanamsa(t)
    earth = eph['earth']
    
    # Для определения ретроградности (сравнение текущего момента и момента через 0.01 дня)
    t2 = ts.tt_jd(t.tt + 0.01)
    
    planets_objects = {
        'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 
        'Mercury': eph['mercury'], 'Jupiter': eph['jupiter_barycenter'], 
        'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']
    }
    
    res = []
    for name, obj in planets_objects.items():
        pos1 = earth.at(t).observe(obj).ecliptic_latlon()
        pos2 = earth.at(t2).observe(obj).ecliptic_latlon()
        
        lon = (pos1[1].degrees - current_ayan) % 360
        is_retro = pos2[1].degrees < pos1[1].degrees
        
        deg_in_sign = lon % 30
        # ИСПРАВЛЕНИЕ: Для ретроградных планет (кроме Светил) АК считается от 30 назад
        eff_deg = (30 - deg_in_sign) if (is_retro and name not in ['Sun', 'Moon']) else deg_in_sign
        
        res.append({'Planet': name, 'Lon': lon, 'Deg': deg_in_sign, 'EffDeg': eff_deg, 'Retro': is_retro})
    
    # Сортировка по ЭФФЕКТИВНОМУ градусу (учитывая ретроградность)
    df_ak = pd.DataFrame(res).sort_values(by='EffDeg', ascending=False).reset_index(drop=True)
    roles = ['AK', 'AmK', 'BK', 'MK', 'PiK', 'PK', 'GK']
    df_ak['Role'] = roles[:len(df_ak)]
    
    T = (t.tt - 2451545.0) / 36525.0
    node_mean_lon = (125.0445550 - 1934.1361849 * T + 0.0020762 * T**2) % 360
    ra_lon = (node_mean_lon - current_ayan) % 360
    
    df_nodes = pd.DataFrame([
        {'Planet': 'Rahu', 'Lon': ra_lon, 'Deg': ra_lon % 30, 'Role': '-'},
        {'Planet': 'Ketu', 'Lon': (ra_lon + 180) % 360, 'Deg': (ra_lon + 180) % 30, 'Role': '-'}
    ])
    
    return pd.concat([df_ak, df_nodes], ignore_index=True), current_ayan

def get_lunar_info(t):
    """ТВОЯ ФУНКЦИЯ + Moon Visualizer и Сизигий"""
    earth = eph['earth']
    s_lon = earth.at(t).observe(eph['sun']).ecliptic_latlon()[1].degrees
    m_lon = earth.at(t).observe(eph['moon']).ecliptic_latlon()[1].degrees
    diff = (m_lon - s_lon) % 360
    tithi = math.ceil(diff / 12) or 1
    
    # Moon Visualizer: Динамическая иконка
    icons = ["🌑","🌒","🌓","🌔","🌕","🌖","🌗","🌘"]
    icon = icons[int(((diff + 22.5) % 360) / 45)]
    
    status = "Растущая (Шукла)" if diff < 180 else "Убывающая (Кришна)"
    
    # Расчет до ближайшего Полнолуния (180) или Новолуния (360)
    target = 180 if diff < 180 else 360
    hours_to_go = (target - diff) / 0.508 # ср. скорость
    
    return tithi, status, icon, hours_to_go

def get_full_info(row):
    nak_idx = int(row['Lon'] / (360/27)) % 27
    sign = ZODIAC_SIGNS[int(row['Lon'] / 30)]
    retro_mark = " (R)" if row.get('Retro') else ""
    return f"{P_ICONS.get(row['Planet'], row['Planet'])}{retro_mark} | {Z_ICONS.get(sign, sign)} | ☸️ {NAKSHATRAS[nak_idx]}"

# (Остальные твои функции отрисовки HTML и стилей остаются без изменений)

# --- ИНТЕРФЕЙС ---
if 's_dt' not in st.session_state: st.session_state.s_dt = datetime.now()
if 'e_dt' not in st.session_state: st.session_state.e_dt = datetime.now() + timedelta(days=2)

st.markdown('<h1 style="text-align:center;">Julia Assistant Astro Coordination Center</h1>', unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📊 Прямой эфир", "📅 Высокоточный Таймлайн"])

with tab1:
    now_utc = datetime.utcnow()
    t_now = ts.utc(now_utc.year, now_utc.month, now_utc.day, now_utc.hour, now_utc.minute, now_utc.second)
    df, ayan_val = get_planet_data(t_now)
    tithi, l_status, l_icon, h_to_siz = get_lunar_info(t_now)

    # Динамический блок "Совет для Хозяина"
    advice_text = "Экадаши: время поста и молитвы" if tithi in [11, 26] else "Благоприятное время для текущих дел"
    
    st.markdown(f"""
    <div style="display: flex; gap: 10px; margin-bottom: 20px;">
        <div style="flex: 1; background: #f8f9fa; border-left: 5px solid #1B263B; padding: 15px; border-radius: 10px; border: 1px solid #dee2e6;">
            <h3 style="margin:0;">{l_icon} Лунный цикл</h3>
            <p style="margin:5px 0;"><b>Титхи:</b> {tithi} | <b>До Сизигия:</b> {int(h_to_siz)}ч</p>
        </div>
        <div style="flex: 1; background: #eef2f3; border-left: 5px solid #415A77; padding: 15px; border-radius: 10px; border: 1px solid #dee2e6;">
            <h3 style="margin:0;">💡 Совет для Хозяина</h3>
            <p style="margin:5px 0;">{advice_text}</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.table(df[['Role', 'Planet', 'Deg']])
    st.metric("💎 АК (Атма-карака)", get_full_info(df.iloc[0]))
    st.metric("🥈 AmK (Аматья-карака)", get_full_info(df.iloc[1]))

with tab2:
    # --- Оптимизированный расчет ---
    if st.button('🚀 Рассчитать периоды'):
        curr = st.session_state.s_dt - timedelta(hours=3)
        end = st.session_state.e_dt - timedelta(hours=3)
        events = []
        last_pair = None

        with st.spinner('Анализ движения планет...'):
            while curr < end:
                t_check = ts.utc(curr.year, curr.month, curr.day, curr.hour, curr.minute)
                df_c, _ = get_planet_data(t_check)
                current_pair = f"{df_c.iloc[0]['Planet']}/{df_c.iloc[1]['Planet']}"
                
                if last_pair and current_pair != last_pair:
                    # Уточнение минуты в найденном часовом интервале
                    for m in range(60):
                        t_fine = curr - timedelta(minutes=60-m)
                        ts_f = ts.utc(t_fine.year, t_fine.month, t_fine.day, t_fine.hour, t_fine.minute)
                        df_f, _ = get_planet_data(ts_f)
                        if f"{df_f.iloc[0]['Planet']}/{df_f.iloc[1]['Planet']}" == current_pair:
                            events.append({
                                "Время (Сочи)": (t_fine + timedelta(hours=3)).strftime("%d.%m.%Y %H:%M"),
                                "АК": get_full_info(df_f.iloc[0]),
                                "AmK": get_full_info(df_f.iloc[1])
                            })
                            break
                
                last_pair = current_pair
                curr += timedelta(hours=1) # Быстрый шаг

        st.table(pd.DataFrame(events))
