import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta, time
import pandas as pd
import streamlit.components.v1 as components
import math
import os
import base64

# ============================================================
# ⛔ БЛОК 1: ФУНДАМЕНТ (БАЗОВЫЕ НАСТРОЙКИ И ДВИЖОК)
# ============================================================
st.set_page_config(page_title="Julia Assistant Astro Coordination Center", layout="wide")

@st.cache_resource
def init_engine():
    ts = load.timescale()
    eph = load('de421.bsp')
    return ts, eph

ts, eph = init_engine()

# --- СЛОВАРИ И КОНСТАНТЫ ---
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]
NAK_LORDS = ["Кету", "Венера", "Солнце", "Луна", "Марс", "Раху", "Юпитер", "Сатурн", "Меркурий"] * 3
P_ICONS = {'Sun': '☀️ Sun', 'Moon': '🌙 Moon', 'Mars': '🔴 Mars', 'Mercury': '☿️ Merc', 'Jupiter': '🔵 Jup', 'Venus': '♀️ Venus', 'Saturn': '🪐 Sat'}
Z_ICONS = {"Овен": "♈ Овен", "Телец": "♉ Телец", "Близнецы": "♊ Близн", "Рак": "♋ Рак", "Лев": "♌ Лев", "Дева": "♍ Дева", "Весы": "♎ Весы", "Скорпион": "♏Скорп", "Стрелец": "♐ Стрел", "Козерог": "♑Козег", "Водолей": "♒ Водол", "Рыбы": "♓ Рыбы"}

# ============================================================
# ⛔ БЛОК 2: МАТЕМАТИЧЕСКОЕ ЯДРО (РАСЧЕТЫ И АСТРО-ЛОГИКА)
# ============================================================
def get_dynamic_ayanamsa(t):
    T = (t.tt - 2451545.0) / 36525.0
    return 23.856235 + (2.30142 * T) + (0.000139 * T**2)

def get_planet_data(t):
    ayan = get_dynamic_ayanamsa(t)
    earth = eph['earth']
    planets_objects = {'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 'Mercury': eph['mercury'], 'Jupiter': eph['jupiter_barycenter'], 'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']}
    res = []
    for name, obj in planets_objects.items():
        lon = (earth.at(t).observe(obj).ecliptic_latlon()[1].degrees - ayan) % 360
        res.append({'Planet': name, 'Lon': lon, 'Deg': lon % 30})
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    df['Role'] = ['AK', 'AmK', 'BK', 'MK', 'PiK', 'GK', 'DK'][:len(df)]
    ra_lon = (earth.at(t).observe(eph['moon']).ecliptic_latlon()[1].degrees - ayan + 180) % 360 
    ra_deg = 30 - (ra_lon % 30) 
    return df, ra_lon, ra_deg

def get_lunar_data(t):
    sun_lon = eph['earth'].at(t).observe(eph['sun']).ecliptic_latlon()[1].degrees
    moon_lon = eph['earth'].at(t).observe(eph['moon']).ecliptic_latlon()[1].degrees
    diff = (moon_lon - sun_lon) % 360
    tithi = int(diff / 12) + 1
    status = "Растущая (Шукла)" if diff < 180 else "Убывающая (Кришна)"
    icon = ["🌑","🌒","🌓","🌔","🌕","🌖","🌗","🌘"][int(diff/45) % 8]
    return tithi, status, icon

def get_xau_storms(dt_start, days=45):
    storms = []
    earth = eph['earth']
    for i in range(days):
        check_date = dt_start + timedelta(days=i)
        t_check = ts.utc(check_date.year, check_date.month, check_date.day)
        ayan = get_dynamic_ayanamsa(t_check)
        sun_lon = (earth.at(t_check).observe(eph['sun']).ecliptic_latlon()[1].degrees - ayan) % 360
        _, ra_lon_check, _ = get_planet_data(t_check)
        diff = abs(sun_lon - ra_lon_check) % 360
        for p in [0, 90, 180, 270]:
            if abs(diff - p) < 3:
                storms.append({"Дата": check_date.strftime("%d.%m"), "Тип": "⚠️ ШТОРМ" if p in [0, 180] else "⚡️ ВОЛАТИЛЬНОСТЬ", "Угол": f"{int(p)}°"})
                break
    seen, unique = set(), []
    for s in storms:
        if s["Дата"] not in seen:
            unique.append(s); seen.add(s["Дата"])
    return unique[:5]

def get_full_info(row):
    sign = ZODIAC_SIGNS[int(row['Lon']/30)]
    return f"{P_ICONS.get(row['Planet'], row['Planet'])} | {Z_ICONS.get(sign, sign)} {row['Deg']:.2f}°"
NAK_SYMBOLS = {
    "Ашвини": "🐎", "Бхарани": "♈", "Криттика": "🔪", "Рохини": "🛒", "Мригашира": "🦌",
    "Аридра": "💧", "Пунарвасу": "🏹", "Пушья": "🐄", "Ашлеша": "🐍", "Магха": "🏰",
    "Пурва-пх": "🛋️", "Уттара-пх": "🛌", "Хаста": "🖐️", "Читра": "💎", "Свати": "🌱",
    "Вишакха": "⚖️", "Анурадха": "🌸", "Джьештха": "🛡️", "Мула": "🪵", "Пурва-аш": "🐘",
    "Уттара-аш": "🐘", "Шравана": "👂", "Дхаништха": "🥁", "Шатабхиша": "⚪", "Пурва-бх": "⚔️",
    "Уттара-бх": "👑", "Ревати": "🐟"
}

# Функция для красивого вывода полной инфо о планете
def get_extended_info(row):
    sign_idx = int(row['Lon']/30)
    sign = ZODIAC_SIGNS[sign_idx]
    nak_idx = int(row['Lon']/(360/27)) % 27
    nak_name = NAKSHATRAS[nak_idx]
    nak_lord = NAK_LORDS[nak_idx]
    symbol = NAK_SYMBOLS.get(nak_name, "✨")
    
    return {
        "full_name": f"{P_ICONS.get(row['Planet'], row['Planet'])}",
        "position": f"{Z_ICONS.get(sign, sign)} {row['Deg']:.2f}°",
        "nakshatra": f"{symbol} {nak_name} ({nak_lord})"
    }
# ============================================================
# ⛔ БЛОК 3: ШАПКА, ЛОГОТИП И ЧАСЫ
# ============================================================
col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
with col_l2:
    if os.path.exists("logo.png"):
        st.image("logo.png", width='stretch')

st.markdown("""
<style>
    .julia-title { text-align: center; margin-top: -10px; margin-bottom: 25px; font-weight: 800; font-size: 3.2em; 
    background: linear-gradient(270deg, #0D1B2A, #1B263B, #415A77, #0D1B2A); background-size: 400% 400%; 
    -webkit-background-clip: text; -webkit-text-fill-color: transparent; animation: dark-glow 10s ease infinite; }
    @keyframes dark-glow { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
</style>
<h1 class="julia-title">Julia Assistant Astro Coordination Center</h1>
""", unsafe_allow_html=True)

st.iframe("""
    <div style="background: linear-gradient(90deg, #050510, #0a0a20); padding:15px; border-radius:15px; text-align:center; font-family: sans-serif; border: 1px solid #1B263B;">
        <h2 id="clock" style="margin:0; color:#415A77; letter-spacing: 2px;">Загрузка...</h2>
        <p style="margin:0; color:#778DA9; font-size: 0.8em; text-transform: uppercase;">Sochi Astro-Coordination Time (UTC+3)</p>
    </div>
    <script>
        function updateClock() { let d = new Date(); let utc = d.getTime() + (d.getTimezoneOffset() * 60000); let sochi = new Date(utc + (3600000 * 3)); document.getElementById('clock').innerHTML = sochi.toLocaleTimeString('ru-RU'); }
        setInterval(updateClock, 1000); updateClock();
    </script>
""", height=110)

# ============================================================
# ⛔ БЛОК 4: ОПЕРАТИВНЫЙ МОНИТОРИНГ (ИНТЕРФЕЙС И РОТАЦИИ)
# ============================================================

# Сначала создаем табы, чтобы избежать NameError
tab1, tab2 = st.tabs(["📊 Прямой эфир", "📅 Высокоточный Планировщик"])

with tab1:
    now_utc = datetime.utcnow()
    t_now = ts.utc(now_utc.year, now_utc.month, now_utc.day, now_utc.hour, now_utc.minute, now_utc.second)
    df, ra_lon, ra_deg = get_planet_data(t_now)
    tithi, l_status, l_icon = get_lunar_data(t_now)
    
    # --- 1. Секция Раху и Луны (Компактно) ---
    col_top1, col_top2 = st.columns([2, 1])
    with col_top1:
        if ra_deg < 2 or ra_deg > 28: color = "#FF4B4B"; status = "ГАНДАНТА"
        elif ra_deg < 5 or ra_deg > 25: color = "#FFA500"; status = "РИСК"
        else: color = "#00C853"; status = "НОРМА"
        st.markdown(f"""<div style="padding:10px; border-radius:10px; border:1px solid {color}; background:{color}11;">
            <span style="color:{color}; font-weight:bold;">🐲 RAHU {status}: {ra_deg:.2f}°</span></div>""", unsafe_allow_html=True)
    with col_top2:
        st.markdown(f"""<div style="padding:10px; border-radius:10px; border:1px solid #415A77; text-align:center;">
            {l_icon} {tithi} титхи</div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- 2. Мониторинг Ротаций (АК и АмК) ---
    st.subheader("🔄 Текущая конфигурация ротаций")
    
    # Получаем расширенные данные для АК и АмК
    def get_card_data(row):
        sign_idx = int(row['Lon']/30)
        nak_idx = int(row['Lon']/(360/27)) % 27
        return {
            "name": f"{P_ICONS.get(row['Planet'], row['Planet'])}",
            "pos": f"{Z_ICONS.get(ZODIAC_SIGNS[sign_idx], ZODIAC_SIGNS[sign_idx])} {row['Deg']:.2f}°",
            "nak": f"{NAK_SYMBOLS.get(NAKSHATRAS[nak_idx], '✨')} {NAKSHATRAS[nak_idx]} ({NAK_LORDS[nak_idx]})"
        }

    ak_info = get_card_data(df.iloc[0])
    amk_info = get_card_data(df.iloc[1])
    ak_name, amk_name = df.iloc[0]['Planet'], df.iloc[1]['Planet']

    # Расчет прогресса (сканирование границ)
    with st.spinner("Синхронизация времени ротации..."):
        s_time, e_time = now_utc, now_utc
        # Назад
        for m in range(0, 2880, 15):
            t_c = ts.utc((now_utc - timedelta(minutes=m)).year, (now_utc - timedelta(minutes=m)).month, (now_utc - timedelta(minutes=m)).day, (now_utc - timedelta(minutes=m)).hour, (now_utc - timedelta(minutes=m)).minute)
            df_c, _, _ = get_planet_data(t_c)
            if df_c.iloc[0]['Planet'] != ak_name or df_c.iloc[1]['Planet'] != amk_name:
                s_time = now_utc - timedelta(minutes=m); break
        # Вперед
        for m in range(0, 2880, 15):
            t_c = ts.utc((now_utc + timedelta(minutes=m)).year, (now_utc + timedelta(minutes=m)).month, (now_utc + timedelta(minutes=m)).day, (now_utc + timedelta(minutes=m)).hour, (now_utc + timedelta(minutes=m)).minute)
            df_c, _, _ = get_planet_data(t_c)
            if df_c.iloc[0]['Planet'] != ak_name or df_c.iloc[1]['Planet'] != amk_name:
                e_time = now_utc + timedelta(minutes=m); break

        total = (e_time - s_time).total_seconds()
        current = (now_utc - s_time).total_seconds()
        prog_val = min(max(current / total, 0.0), 1.0) if total > 0 else 0.5

    # Визуальные карточки
    col_ak, col_amk = st.columns(2)
    for col, info, title, b_color in zip([col_ak, col_amk], [ak_info, amk_info], ["💎 ATMAKARAKA", "🥈 AMATYAKARAKA"], ["#415A77", "#778DA9"]):
        with col:
            st.markdown(f"""<div style="background:#0D1B2A; padding:15px; border-radius:10px; border-top: 4px solid {b_color}; min-height:140px;">
                <small style="color:{b_color}; letter-spacing:1px;">{title}</small><br>
                <b style="font-size:1.5em; color:white;">{info['name']}</b><br>
                <code style="color:#E0E1DD;">{info['pos']}</code><br>
                <div style="margin-top:8px; font-size:0.95em; color:#A9D6E5;">{info['nak']}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown(f"<p style='margin: 15px 0 -10px 0; font-size:0.8em; text-align:center; color:#778DA9;'>Завершено: {int(prog_val*100)}% ротации</p>", unsafe_allow_html=True)
    st.progress(prog_val)
    st.caption(f"🏁 Начало: {(s_time + timedelta(hours=3)).strftime('%H:%M')} | 🔚 Конец: {(e_time + timedelta(hours=3)).strftime('%H:%M')}")

    st.markdown("---")
    
    # Полная таблица (скрыта по умолчанию)
    with st.expander("📊 Показать все 7 Карак (полный список)"):
        df_full = df.copy()
        df_full['Координаты'] = df_full.apply(lambda r: f"{Z_ICONS[ZODIAC_SIGNS[int(r['Lon']/30)]]} {r['Deg']:.2f}°", axis=1)
        st.dataframe(df_full[['Role', 'Planet', 'Координаты']], width='stretch', hide_index=True)
# ============================================================
# ⛔ БЛОК 5: ПЛАНИРОВЩИК (ВЫСОКОТОЧНЫЙ РАСЧЕТ)
# ============================================================
with tab2:
    st.header("📅 Высокоточный планировщик ротаций")
    c_p1, c_p2 = st.columns(2)
    with c_p1:
        d_s = st.date_input("Дата начала", datetime.now(), key="ds_p")
        t_s = st.time_input("Время начала", time(0, 0), key="ts_p")
    with c_p2:
        d_e = st.date_input("Дата конца", datetime.now() + timedelta(days=3), key="de_p")
        t_e = st.time_input("Время конца", time(23, 59), key="te_p")

    if st.button('🚀 Рассчитать и подготовить бланк'):
        dt_start = datetime.combine(d_s, t_s)
        dt_end = datetime.combine(d_e, t_e)
        curr_utc = dt_start - timedelta(hours=3)
        end_utc = dt_end - timedelta(hours=3)
        events = []
        
        t_init = ts.utc(curr_utc.year, curr_utc.month, curr_utc.day, curr_utc.hour, curr_utc.minute)
        df_i, _, _ = get_planet_data(t_init)
        last_pair = f"{df_i.iloc[0]['Planet']}/{df_i.iloc[1]['Planet']}"
        events.append({"Время (Сочи)": dt_start.strftime("%d.%m.%Y %H:%M"), "💎 АК": get_full_info(df_i.iloc[0]), "🥈 AmK": get_full_info(df_i.iloc[1])})

        while curr_utc < end_utc:
            curr_utc += timedelta(minutes=5)
            t_s_loop = ts.utc(curr_utc.year, curr_utc.month, curr_utc.day, curr_utc.hour, curr_utc.minute)
            df_s, _, _ = get_planet_data(t_s_loop)
            new_pair = f"{df_s.iloc[0]['Planet']}/{df_s.iloc[1]['Planet']}"
            if new_pair != last_pair:
                events.append({"Время (Сочи)": (curr_utc + timedelta(hours=3)).strftime("%d.%m.%Y %H:%M"), "💎 АК": get_full_info(df_s.iloc[0]), "🥈 AmK": get_full_info(df_s.iloc[1])})
                last_pair = new_pair
        st.table(pd.DataFrame(events))
