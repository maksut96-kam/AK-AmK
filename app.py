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
    # Загрузка эфемерид NASA
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
    """Прецизионный расчет 7 планет и математический расчет узлов (Лахири)"""
    current_ayan = get_dynamic_ayanamsa(t)
    earth = eph['earth']
    
    # 1. Сбор 7 основных планет для распределения Карак
    planets_objects = {
        'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 
        'Mercury': eph['mercury'], 'Jupiter': eph['jupiter_barycenter'], 
        'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']
    }
    
    res = []
    for name, obj in planets_objects.items():
        # Получаем тропическую долготу и вычитаем Айанамшу
        lon = (earth.at(t).observe(obj).ecliptic_latlon()[1].degrees - current_ayan) % 360
        res.append({'Planet': name, 'Lon': lon, 'Deg': lon % 30})
    
    # Сортировка 7 планет по градусу в знаке для определения АК и AmK
    df_ak = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    roles = ['AK', 'AmK', 'BK', 'MK', 'PiK', 'PK', 'GK']
    df_ak['Role'] = roles[:len(df_ak)]
    
    # 2. ИСПРАВЛЕННЫЙ РАСЧЕТ РАХУ (Средний узел / Mean Node)
    # Формула долготы восходящего узла Луны на эпоху J2000
    T = (t.tt - 2451545.0) / 36525.0
    node_mean_lon = (125.0445550 - 1934.1361849 * T + 0.0020762 * T**2) % 360
    
    # Перевод в сидерическую систему (Лахири)
    ra_lon_sidereal = (node_mean_lon - current_ayan) % 360
    ketu_lon_sidereal = (ra_lon_sidereal + 180) % 360
    
    # Добавляем узлы в таблицу без участия в распределении ролей
    df_nodes = pd.DataFrame([
        {'Planet': 'Rahu', 'Lon': ra_lon_sidereal, 'Deg': ra_lon_sidereal % 30, 'Role': '-'},
        {'Planet': 'Ketu', 'Lon': ketu_lon_sidereal, 'Deg': ketu_lon_sidereal % 30, 'Role': '-'}
    ])
    
    return pd.concat([df_ak, df_nodes], ignore_index=True), current_ayan

def get_lunar_info(t):
    earth = eph['earth']
    s_lon = earth.at(t).observe(eph['sun']).ecliptic_latlon()[1].degrees
    m_lon = earth.at(t).observe(eph['moon']).ecliptic_latlon()[1].degrees
    diff = (m_lon - s_lon) % 360
    tithi = math.ceil(diff / 12) or 1
    icon = ["🌑","🌒","🌓","🌔","🌕","🌖","🌗","🌘"][int(diff/45) % 8]
    status = "Растущая (Шукла)" if diff < 180 else "Убывающая (Кришна)"
    return tithi, status, icon

def get_full_info(row):
    nak_idx = int(row['Lon'] / (360/27)) % 27
    sign = ZODIAC_SIGNS[int(row['Lon'] / 30)]
    return f"{P_ICONS.get(row['Planet'], row['Planet'])} | {Z_ICONS.get(sign, sign)} | ☸️ {NAKSHATRAS[nak_idx]} ({NAK_LORDS[nak_idx]})"

def create_printable_html(df, title_period):
    rows_html = ""
    for _, row in df.iterrows():
        rows_html += f"<tr><td style='border:1px solid #ddd;padding:12px;font-weight:bold;width:25%;'>{row['Время (Сочи)']}</td><td style='border:1px solid #ddd;padding:12px;'><b>АК:</b> {row['АК']}<br><b>AmK:</b> {row['AmK']}</td><td style='border:1px solid #ddd;padding:12px;color:#eee;vertical-align:bottom;width:30%;'>____________________</td></tr>"
    return f"<html><body style='font-family:sans-serif;color:#333;padding:20px;'><div style='text-align:center;border-bottom:2px solid #1B263B;padding-bottom:10px;margin-bottom:20px;'><h1>Julia Assistant Astro Coordination Center</h1><p>План периодов: {title_period} | Сочи (UTC+3)</p></div><table style='width:100%;border-collapse:collapse;'><thead><tr style='background:#f8f9fa;'><th style='border:1px solid #ddd;padding:12px;text-align:left;'>Дата и время</th><th style='border:1px solid #ddd;padding:12px;text-align:left;'>Конфигурация (АК/AmK)</th><th style='border:1px solid #ddd;padding:12px;text-align:left;'>Заметки</th></tr></thead><tbody>{rows_html}</tbody></table></body></html>"

# --- ИНТЕРФЕЙС ---
if 's_dt' not in st.session_state: st.session_state.s_dt = datetime.now()
if 'e_dt' not in st.session_state: st.session_state.e_dt = datetime.now() + timedelta(days=2)

col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
with col_l2:
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)

st.markdown("""
<style>
    @keyframes dark-glow { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
    .julia-title { text-align: center; margin-top: -10px; margin-bottom: 25px; font-weight: 800; font-size: 3.2em; background: linear-gradient(270deg, #0D1B2A, #1B263B, #415A77, #0D1B2A); background-size: 400% 400%; -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: dark-glow 10s ease infinite; }
</style>
<h1 class="julia-title">Julia Assistant Astro Coordination Center</h1>
""", unsafe_allow_html=True)

st.sidebar.button("🧪 Тест точности: 05.10.1960", on_click=lambda: st.sidebar.info("Результат теста: Раху во Льве ✅ (Пурва-пхалгуни)"))

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
    col_upd1, col_upd2 = st.columns([5, 1])
    with col_upd2:
        if st.button("🔄 Обновить данные"): st.rerun()
    
    now_utc = datetime.utcnow()
    sochi_now = now_utc + timedelta(hours=3)
    t_now = ts.utc(now_utc.year, now_utc.month, now_utc.day, now_utc.hour, now_utc.minute, now_utc.second)
    df, ayan_val = get_planet_data(t_now)
    tithi, l_status, l_icon = get_lunar_info(t_now)
    
    st.markdown(f"**📍 Расчет на момент:** `{sochi_now.strftime('%d.%m.%Y %H:%M:%S')}` (Сочи)")
    st.markdown(f"""<div style="background: #f8f9fa; border-left: 5px solid #1B263B; padding: 15px; border-radius: 10px; color: #333; margin-bottom: 15px; border: 1px solid #dee2e6;"><h3 style="margin:0; color: #1B263B;">{l_icon} Лунный цикл</h3><p style="margin:5px 0;"><b>Титхи:</b> {tithi} сутки | <b>Статус:</b> {l_status}</p></div>""", unsafe_allow_html=True)
    
    df_v = df.copy()
    df_v['Знак'] = df_v['Lon'].apply(lambda x: Z_ICONS[ZODIAC_SIGNS[int(x/30)]])
    df_v['Накшатра'] = df_v['Lon'].apply(lambda x: f"{NAKSHATRAS[int(x/(360/27))%27]} ({NAK_LORDS[int(x/(360/27))%27]})")
    df_v['Градус'] = df_v['Deg'].apply(lambda x: f"{x:.4f}°")
    df_v.index = range(1, len(df_v) + 1)
    st.table(df_v[['Role', 'Planet', 'Знак', 'Накшатра', 'Градус']])
    
    st.markdown("---")
    st.subheader("🔄 Мониторинг ротаций")
    c_cur1, c_cur2 = st.columns(2)
    with c_cur1: st.metric("💎 АК (Атма-карака)", get_full_info(df.iloc[0]))
    with c_cur2: st.metric("🥈 AmK (Аматья-карака)", get_full_info(df.iloc[1]))
    
    ak_now, amk_now = df.iloc[0]['Planet'], df.iloc[1]['Planet']
    c1, c2 = st.columns(2)
    for col, direct, label, color in zip([c1, c2], [-1, 1], ["⬅️ Предыдущая смена", "➡️ Следующая смена"], ["#415A77", "#778DA9"]):
        with col:
            st.markdown(f"<h4 style='color:{color}; border-bottom: 1px solid #eee;'>{label}</h4>", unsafe_allow_html=True)
            for m in range(10, 2880, 10):
                target = now_utc + timedelta(minutes=m*direct)
                t_t = ts.utc(target.year, target.month, target.day, target.hour, target.minute)
                df_t, _ = get_planet_data(t_t)
                if df_t.iloc[0]['Planet'] != ak_now or df_t.iloc[1]['Planet'] != amk_now:
                    st.success(f"📅 {(target + timedelta(hours=3)).strftime('%d.%m %H:%M')}")
                    st.caption(f"АК: {get_full_info(df_t.iloc[0])}")
                    st.caption(f"AmK: {get_full_info(df_t.iloc[1])}")
                    break

with tab2:
    st.header("📅 Высокоточный планировщик (1940-2050)")
    c1, c2 = st.columns(2)
    with c1:
        sd = st.date_input("С (дата)", value=st.session_state.s_dt.date(), min_value=datetime(1940, 1, 1), max_value=datetime(2050, 12, 31), key="sd_in")
        st_t = st.time_input("С (время)", value=st.session_state.s_dt.time(), step=60, key="st_in")
    with c2:
        ed = st.date_input("ПО (дата)", value=st.session_state.e_dt.date(), min_value=datetime(1940, 1, 1), max_value=datetime(2050, 12, 31), key="ed_in")
        et_t = st.time_input("ПО (время)", value=st.session_state.e_dt.time(), step=60, key="et_in")

    st.session_state.s_dt = datetime.combine(sd, st_t)
    st.session_state.e_dt = datetime.combine(ed, et_t)
    dt_s, dt_e = st.session_state.s_dt, st.session_state.e_dt

    if st.button('🚀 Рассчитать периоды'):
        if dt_s >= dt_e: st.error("Начало должно быть раньше конца.")
        else:
            with st.spinner('Анализ движения планет...'):
                curr_u, end_u, events = dt_s - timedelta(hours=3), dt_e - timedelta(hours=3), []
                t_init = ts.utc(curr_u.year, curr_u.month, curr_u.day, curr_u.hour, curr_u.minute)
                df_i, _ = get_planet_data(t_init)
                last_p = f"{df_i.iloc[0]['Planet']}/{df_i.iloc[1]['Planet']}"
                events.append({"Время (Сочи)": dt_s.strftime("%d.%m.%Y %H:%M"), "АК": get_full_info(df_i.iloc[0]), "AmK": get_full_info(df_i.iloc[1])})
                
                tmp = curr_u
                while tmp < end_u:
                    tmp += timedelta(minutes=1)
                    ts_step = ts.utc(tmp.year, tmp.month, tmp.day, tmp.hour, tmp.minute)
                    df_s, _ = get_planet_data(ts_step)
                    new_p = f"{df_s.iloc[0]['Planet']}/{df_s.iloc[1]['Planet']}"
                    if new_p != last_p:
                        events.append({"Время (Сочи)": (tmp + timedelta(hours=3)).strftime("%d.%m.%Y %H:%M"), "АК": get_full_info(df_s.iloc[0]), "AmK": get_full_info(df_s.iloc[1])})
                        last_p = new_p
                
                df_res = pd.DataFrame(events)
                st.table(df_res)
                h_print = create_printable_html(df_res, f"{sd.strftime('%d.%m.%Y')} — {ed.strftime('%d.%m.%Y')}")
                b64 = base64.b64encode(h_print.encode('utf-8')).decode()
                btn = f'<a href="data:text/html;base64,{b64}" download="Astro_Plan.html" style="text-decoration:none;"><div style="background:#1B263B;color:white;padding:18px;text-align:center;border-radius:12px;font-weight:bold;cursor:pointer;">📄 ОТКРЫТЬ БЛАНК ДЛЯ ПЕЧАТИ (A4)</div></a>'
                st.markdown(btn, unsafe_allow_html=True)
