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

def format_deg_to_min(deg_float):
    d = int(deg_float); m = int((deg_float - d) * 60); s = round((((deg_float - d) * 60) - m) * 60, 2)
    return f"{d}° {m}' {s}\""

def get_planet_data(t):
    """Оптимизированный расчет с учетом ретроградности"""
    current_ayan = get_dynamic_ayanamsa(t)
    earth = eph['earth']
    
    # Для проверки ретроградности (скорость)
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
        # ЛОГИКА РЕТРОГРАДНОСТИ: 30 - градус для АК
        eff_deg = (30 - deg_in_sign) if (is_retro and name not in ['Sun', 'Moon']) else deg_in_sign
        
        res.append({'Planet': name, 'Lon': lon, 'Deg': deg_in_sign, 'EffDeg': eff_deg, 'Retro': is_retro})
    
    # Расчет Раху (Mean Node)
    T = (t.tt - 2451545.0) / 36525.0
    ra_mean_lon = (125.0445550 - 1934.1361849 * T + 0.0020762 * T**2) % 360
    ra_lon = (ra_mean_lon - current_ayan) % 360
    
    df = pd.DataFrame(res).sort_values(by='EffDeg', ascending=False).reset_index(drop=True)
    roles = ['AK', 'AmK', 'BK', 'MK', 'PiK', 'PK', 'GK']
    df['Role'] = roles[:len(df)]
    
    ketu_lon = (ra_lon + 180) % 360
    df_nodes = pd.DataFrame([
        {'Planet': 'Rahu', 'Lon': ra_lon, 'Deg': ra_lon % 30, 'Role': '-'},
        {'Planet': 'Ketu', 'Lon': ketu_lon, 'Deg': ketu_lon % 30, 'Role': '-'}
    ])
    
    return pd.concat([df, df_nodes], ignore_index=True), current_ayan

def get_lunar_info(t):
    earth = eph['earth']
    s_lon = earth.at(t).observe(eph['sun']).ecliptic_latlon()[1].degrees
    m_lon = earth.at(t).observe(eph['moon']).ecliptic_latlon()[1].degrees
    diff = (m_lon - s_lon) % 360
    tithi = math.ceil(diff / 12) or 1
    icon = ["🌑","🌒","🌓","🌔","🌕","🌖","🌗","🌘"][int(diff/45) % 8]
    status = "Растущая (Шукла)" if diff < 180 else "Убывающая (Кришна)"
    
    # Расчет до сизигия
    target = 180 if diff < 180 else 360
    hours_to_go = (target - diff) / 0.508
    
    return tithi, status, icon, hours_to_go

# (Функции create_printable_html и get_full_info остаются как в твоем коде)
# ...

# --- ТАЙМЛАЙН (ОПТИМИЗИРОВАННЫЙ) ---
with tab2:
    # ... (твои инпуты дат sd, ed)
    if st.button('🚀 Рассчитать и подготовить бланк'):
        if dt_s >= dt_e: st.error("Начало должно быть раньше конца.")
        else:
            with st.spinner('Высокоточный расчет...'):
                curr = dt_s - timedelta(hours=3)
                end = dt_e - timedelta(hours=3)
                events = []
                last_pair = None
                
                while curr < end:
                    t_step = ts.utc(curr.year, curr.month, curr.day, curr.hour, curr.minute)
                    df_s, _ = get_planet_data(t_step)
                    new_pair = f"{df_s.iloc[0]['Planet']}/{df_s.iloc[1]['Planet']}"
                    
                    if last_pair and new_pair != last_pair:
                        # Если сменилось, ищем минуту внутри этого часа
                        for m in range(60):
                            t_fine = curr - timedelta(minutes=60-m)
                            ts_f = ts.utc(t_fine.year, t_fine.month, t_fine.day, t_fine.hour, t_fine.minute)
                            df_f, _ = get_planet_data(ts_f)
                            if f"{df_f.iloc[0]['Planet']}/{df_f.iloc[1]['Planet']}" == new_pair:
                                events.append({
                                    "Время (Сочи)": (t_fine + timedelta(hours=3)).strftime("%d.%m.%Y %H:%M"),
                                    "АК": get_full_info(df_f.iloc[0]),
                                    "AmK": get_full_info(df_f.iloc[1])
                                })
                                break
                    
                    last_pair = new_pair
                    curr += timedelta(hours=1) # Быстрый шаг
                
                st.table(pd.DataFrame(events))
                # ... (вывод кнопки печати)
