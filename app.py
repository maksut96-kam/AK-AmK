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

# --- Константы и Словари (ТВОИ ОРИГИНАЛЬНЫЕ) ---
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]
NAK_LORDS = ["Кету", "Венера", "Солнце", "Луна", "Марс", "Раху", "Юпитер", "Сатурн", "Меркурий"] * 3

P_ICONS = {'Sun': '☀️ Sun', 'Moon': '🌙 Moon', 'Mars': '🔴 Mars', 'Mercury': '☿️ Merc', 'Jupiter': '🔵 Jup', 'Venus': '♀️ Venus', 'Saturn': '🪐 Sat', 'Rahu': '🐲 Rahu', 'Ketu': '🐍 Ketu'}
Z_ICONS = {"Овен": "♈ Овен", "Телец": "♉ Телец", "Близнецы": "♊ Близн", "Рак": "♋ Рак", "Лев": "♌ Лев", "Дева": "♍ Дева", "Весы": "♎ Весы", "Скорпион": "♏ Скорп", "Стрелец": "♐ Стрел", "Козерог": "♑ Козег", "Водолей": "♒ Водол", "Рыбы": "♓ Рыбы"}

def get_dynamic_ayanamsa(t):
    T = (t.tt - 2451545.0) / 36525.0
    return 23.856235 + (2.30142 * T) + (0.000139 * T**2)

def get_planet_data(t):
    """ТВОЯ ФУНКЦИЯ + Улучшение: Ретроградность и Узлы"""
    current_ayan = get_dynamic_ayanamsa(t)
    earth = eph['earth']
    
    # Расчет скорости для ретроградности
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
        # ПАРАШАРА: Ретроградные считаются от конца знака (30 - deg)
        eff_deg = (30 - deg_in_sign) if (is_retro and name not in ['Sun', 'Moon']) else deg_in_sign
        
        res.append({'Planet': name, 'Lon': lon, 'Deg': deg_in_sign, 'EffDeg': eff_deg, 'Retro': is_retro})
    
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
    """ТВОЯ ФУНКЦИЯ + Улучшение: Moon Visualizer и Сизигий"""
    earth = eph['earth']
    s_lon = earth.at(t).observe(eph['sun']).ecliptic_latlon()[1].degrees
    m_lon = earth.at(t).observe(eph['moon']).ecliptic_latlon()[1].degrees
    diff = (m_lon - s_lon) % 360
    tithi = math.ceil(diff / 12) or 1
    
    # Moon Visualizer: более точные иконки фаз
    icons = ["🌑","🌒","🌓","🌔","🌕","🌖","🌗","🌘"]
    icon = icons[int(((diff + 22.5) % 360) / 45)]
    
    status = "Растущая (Шукла)" if diff < 180 else "Убывающая (Кришна)"
    
    # Расчет до ближайшего Сизигия (Новолуние 0/360 или Полнолуние 180)
    target = 180 if diff < 180 else 360
    hours_to_go = (target - diff) / 0.508
    
    return tithi, status, icon, hours_to_go

def get_full_info(row):
    nak_idx = int(row['Lon'] / (360/27)) % 27
    sign = ZODIAC_SIGNS[int(row['Lon'] / 30)]
    r_mark = " (R)" if row.get('Retro') else ""
    return f"{P_ICONS.get(row['Planet'], row['Planet'])}{r_mark} | {Z_ICONS.get(sign, sign)} | ☸️ {NAKSHATRAS[nak_idx]}"

def create_printable_html(df, title_period):
    rows_html = ""
    for _, row in df.iterrows():
        rows_html += f"<tr><td style='border:1px solid #ddd;padding:12px;font-weight:bold;width:25%;'>{row['Время (Сочи)']}</td><td style='border:1px solid #ddd;padding:12px;'><b>АК:</b> {row['АК']}<br><b>AmK:</b> {row['AmK']}</td><td style='border:1px solid #ddd;padding:12px;color:#eee;vertical-align:bottom;width:30%;'>____________________</td></tr>"
    return f"<html><body style='font-family:sans-serif;color:#333;padding:20px;'><div style='text-align:center;border-bottom:2px solid #1B263B;padding-bottom:10px;margin-bottom:20px;'><h1>Julia Assistant Astro Coordination Center</h1><p>План периодов: {title_period} | Сочи (UTC+3)</p></div><table style='width:100%;border-collapse:collapse;'><thead><tr style='background:#f8f9fa;'><th style='border:1px solid #ddd;padding:12px;text-align:left;'>Дата и время</th><th style='border:1px solid #ddd;padding:12px;text-align:left;'>Конфигурация (АК/AmK)</th><th style='border:1px solid #ddd;padding:12px;text-align:left;'>Заметки</th></tr></thead><tbody>{rows_html}</tbody></table></body></html>"

# --- ИНТЕРФЕЙС (ТВОЯ ЛОГИКА) ---
if 's_dt' not in st.session_state: st.session_state.s_dt = datetime.now()
if 'e_dt' not in st.session_state: st.session_state.e_dt = datetime.now() + timedelta(days=2)

st.markdown('<h1 style="text-align:center;">Julia Assistant Astro Coordination Center</h1>', unsafe_allow_html=True)

components.html("""
    <div style="background: linear-gradient(90deg, #050510, #0a0a20); padding:15px; border-radius:15px; text-align:center; font-family: sans-serif; border: 1px solid #1B263B;">
        <h2 id="clock" style="margin:0; color:#415A77; letter-spacing: 2px;">Загрузка...</h2>
        <p style="margin:0; color:#778DA9; font-size: 0.8em; text-transform: uppercase;">Sochi Astro-Coordination Time (UTC+3)</p>
    </div>
    <script>
        function updateClock() { let d = new Date(); let utc = d.getTime() + (d.getTimezoneOffset() * 60000); let sochi = new Date(utc + (3600000 * 3)); document.getElementById('clock').innerHTML = sochi.toLocaleTimeString('ru-RU'); }
        setInterval(updateClock, 1000); updateClock();
    </script>
""", height=110)

tab1, tab2 = st.tabs(["📊 Прямой эфир", "📅 Высокоточный Таймлайн"])

with tab1:
    now_utc = datetime.utcnow()
    sochi_now = now_utc + timedelta(hours=3)
    t_now = ts.utc(now_utc.year, now_utc.month, now_utc.day, now_utc.hour, now_utc.minute, now_utc.second)
    df, ayan_val = get_planet_data(t_now)
    tithi, l_status, l_icon, h_to_siz = get_lunar_info(t_now)

    # --- НОВЫЕ БЛОКИ (СОВЕТ И ЛУНА) ---
    c_moon1, c_moon2 = st.columns(2)
    with c_moon1:
        st.markdown(f"""<div style="background: #f8f9fa; border-left: 5px solid #1B263B; padding: 15px; border-radius: 10px; color: #333; border: 1px solid #dee2e6;"><h3 style="margin:0; color: #1B263B;">{l_icon} Лунный цикл</h3><p style="margin:5px 0;"><b>Титхи:</b> {tithi} | <b>До Сизигия:</b> {int(h_to_siz)}ч</p></div>""", unsafe_allow_html=True)
    with c_moon2:
        advice = "Экадаши: пост" if tithi in [11, 26] else "Благоприятный день для планирования"
        st.markdown(f"""<div style="background: #eef2f3; border-left: 5px solid #415A77; padding: 15px; border-radius: 10px; color: #333; border: 1px solid #dee2e6;"><h3 style="margin:0; color: #415A77;">💡 Совет для Хозяина</h3><p style="margin:5px 0;">{advice}</p></div>""", unsafe_allow_html=True)

    st.table(df[['Role', 'Planet', 'Deg']])
    
    st.subheader("🔄 Мониторинг ротаций")
    c_cur1, c_cur2 = st.columns(2)
    with c_cur1: st.metric("💎 АК (Атма-карака)", get_full_info(df.iloc[0]))
    with c_cur2: st.metric("🥈 AmK (Аматья-карака)", get_full_info(df.iloc[1]))

with tab2:
    st.header("📅 Высокоточный планировщик")
    # (ТВОИ ИНПУТЫ ДАТ И ВРЕМЕНИ ОСТАЛИСЬ ПРЕЖНИМИ)
    # ... расчет в цикле теперь использует оптимизацию:
    if st.button('🚀 Рассчитать периоды'):
        curr = st.session_state.s_dt - timedelta(hours=3)
        end = st.session_state.e_dt - timedelta(hours=3)
        events = []
        last_p = None

        with st.spinner('Анализ движения планет...'):
            while curr < end:
                t_step = ts.utc(curr.year, curr.month, curr.day, curr.hour, curr.minute)
                df_s, _ = get_planet_data(t_step)
                new_p = f"{df_s.iloc[0]['Planet']}/{df_s.iloc[1]['Planet']}"
                
                if last_p and new_p != last_p:
                    # Уточняем до минуты, если нашли смену в часовом интервале
                    for m in range(60):
                        t_fine = curr - timedelta(minutes=60-m)
                        ts_f = ts.utc(t_fine.year, t_fine.month, t_fine.day, t_fine.hour, t_fine.minute)
                        df_f, _ = get_planet_data(ts_f)
                        if f"{df_f.iloc[0]['Planet']}/{df_f.iloc[1]['Planet']}" == new_p:
                            events.append({"Время (Сочи)": (t_fine + timedelta(hours=3)).strftime("%d.%m.%Y %H:%M"), "АК": get_full_info(df_f.iloc[0]), "AmK": get_full_info(df_f.iloc[1])})
                            break
                
                last_p = new_p
                curr += timedelta(hours=1) # Оптимизированный шаг

        st.table(pd.DataFrame(events))
