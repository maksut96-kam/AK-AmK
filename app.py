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

# Дополненный справочник (название символа + эмодзи)
NAK_SYMBOLS_DETAILED = {
    "Ашвини": "Лошадь 🐎", "Бхарани": "Йони ♈", "Криттика": "Бритва 🔪", "Рохини": "Повозка 🛒", 
    "Мригашира": "Олень 🦌", "Аридра": "Слеза 💧", "Пунарвасу": "Лук 🏹", "Пушья": "Вымя 🐄", 
    "Ашлеша": "Змея 🐍", "Магха": "Трон 🏰", "Пурва-пх": "Гамак 🛋️", "Уттара-пх": "Кровать 🛌", 
    "Хаста": "Кисть 🖐️", "Читра": "Алмаз 💎", "Свати": "Росток 🌱", "Вишакха": "Арка ⚖️", 
    "Анурадха": "Цветок 🌸", "Джьештха": "Серьга 🛡️", "Мула": "Корень 🪵", "Пурва-аш": "Бивень 🐘", 
    "Уттара-аш": "Бивень 🐘", "Шравана": "Ухо 👂", "Дхаништха": "Барабан 🥁", "Шатабхиша": "Круг ⚪", 
    "Пурва-бх": "Мечи ⚔️", "Уттара-бх": "Близнецы 👑", "Ревати": "Рыба 🐟"
}

ROLE_RU = {
    "AK": "АК (Атма-карака)", "AmK": "АмК (Аматья-карака)", "BK": "БК (Бхатри-карака)",
    "MK": "МК (Матри-карака)", "PiK": "ПиК (Питри-карака)", "GK": "ГК (Гнати-карака)", "DK": "ДК (Дара-карака)"
}

# Полные названия планет
P_FULL_NAMES = {
    'Sun': '☀️ Солнце (Sun)', 'Moon': '🌙 Луна (Moon)', 'Mars': '🔴 Марс (Mars)', 
    'Mercury': '☿️ Меркурий (Mercury)', 'Jupiter': '🔵 Юпитер (Jupiter)', 
    'Venus': '♀️ Венера (Venus)', 'Saturn': '🪐 Сатурн (Saturn)'
}

# Чистые списки без сокращений
PURE_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
PURE_ICONS = ["♈", "♉", "♊", "♋", "♌", "♍", "♎", "♏", "♐", "♑", "♒", "♓"]

def get_extended_info(row):
    sign_idx = int(row['Lon']/30)
    nak_idx = int(row['Lon']/(360/27)) % 27
    nak_name = NAKSHATRAS[nak_idx]
    
    return {
        "role_ru": ROLE_RU.get(row['Role'], row['Role']),
        "planet_full": P_FULL_NAMES.get(row['Planet'], row['Planet']),
        "sign_only": PURE_SIGNS[sign_idx],
        "sign_icon": PURE_ICONS[sign_idx],
        "degree": f"{row['Deg']:.4f}°",
        "nak_full": f"{nak_name} ({NAK_LORDS[nak_idx]})",
        "nak_sym": NAK_SYMBOLS_DETAILED.get(nak_name, "✨")
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
# ⛔ БЛОК 4: МОНИТОРИНГ РОТАЦИЙ (ПОЛНАЯ ВЕРСИЯ)
# ============================================================
tab1, tab2 = st.tabs(["📊 Прямой эфир", "📅 Высокоточный Планировщик"])

with tab1:
    now_utc = datetime.utcnow()
    t_now = ts.utc(now_utc.year, now_utc.month, now_utc.day, now_utc.hour, now_utc.minute, now_utc.second)
    df, ra_lon, ra_deg = get_planet_data(t_now)
    tithi, l_status, l_icon = get_lunar_data(t_now)
    
   # --- 1. МОНИТОР РАХУ (ПРОФЕССИОНАЛЬНАЯ ВЕРСИЯ) ---
    st.markdown("### 🐲 Оперативный монитор Раху")
    
    # Логика определения статуса
    if ra_deg < 2 or ra_deg > 28: 
        label, color, bg_color, desc = "КРИТИЧЕСКИЙ ХАОС", "#FF4B4B", "#311717", "ГАНДАНТА: Максимальная иррациональность. Технический анализ не приоритетен."
    elif ra_deg < 5 or ra_deg > 25: 
        label, color, bg_color, desc = "ПОВЫШЕННЫЙ РИСК", "#FFA500", "#332616", "ОПАСНАЯ ЗОНА: Возможны резкие манипуляции и ложные пробои."
    else: 
        label, color, bg_color, desc = "ТЕХНИЧНЫЙ РЫНОК", "#00C853", "#162B1D", "ЧИСТАЯ ЗОНА: Рынок предсказуем, уровни отрабатывают штатно."

    # Расчет "Давления" (чем ближе к краям знака, тем выше процент)
    pressure_val = (30 - ra_deg) * 3.33 if ra_deg > 15 else (ra_deg) * 3.33 # Примерная логика инверсии для Ганданты
    pressure_pct = min(max(int(100 - (ra_deg * 3.33) if ra_deg < 15 else (ra_deg - 15) * 6.66), 5), 100)

    # HTML Виджет Раху
    st.markdown(f"""
    <div style="background-color: {bg_color}; border: 1px solid {color}; padding: 20px; border-radius: 12px; margin-bottom: 20px;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <span style="color: {color}; font-size: 1.4em; font-weight: bold;">{label}</span>
            <span style="color: white; font-size: 1.2em; font-family: monospace; background: rgba(255,255,255,0.1); padding: 4px 10px; border-radius: 6px;">{ra_deg:.4f}°</span>
        </div>
        <p style="color: #E0E1DD; margin-top: 10px; font-size: 1.1em; line-height: 1.4;">{desc}</p>
        <div style="margin-top: 15px;">
            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                <span style="font-size: 0.9em; color: #778DA9;">ИНДЕКС ДАВЛЕНИЯ (XAU/USD)</span>
                <span style="font-size: 0.9em; color: {color}; font-weight: bold;">{pressure_pct}%</span>
            </div>
            <div style="width: 100%; background-color: #1B263B; border-radius: 5px; height: 10px;">
                <div style="width: {pressure_pct}%; background-color: {color}; height: 10px; border-radius: 5px; transition: width 0.5s;"></div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Ближайшие штормы волатильности (компактный список)
    storms = get_xau_storms(now_utc)
    if storms:
        with st.expander("⚡ Календарь ближайших штормов (45 дней)"):
            cols = st.columns(len(storms))
            for idx, s in enumerate(storms):
                with cols[idx]:
                    st.markdown(f"""
                    <div style="text-align: center; background: #0D1B2A; padding: 10px; border-radius: 8px; border: 1px solid #415A77;">
                        <small style="color: #778DA9;">{s['Дата']}</small><br>
                        <b style="font-size: 0.9em;">{s['Тип']}</b><br>
                        <code style="color: #A9D6E5;">{s['Угол']}</code>
                    </div>
                    """, unsafe_allow_html=True)

    # --- 2. ТЕКУЩАЯ АК И АМК (КАРТОЧКИ) ---
    st.subheader("🔄 Текущая АК и AmK")
    ak_data = get_extended_info(df.iloc[0]) 
    amk_data = get_extended_info(df.iloc[1])
    
    c_ak, c_amk = st.columns(2)
    with c_ak:
        st.markdown(f"""<div style="background:#0D1B2A; padding:20px; border-radius:10px; border-top: 4px solid #415A77; min-height:170px;">
            <small style="color:#415A77; font-weight:bold;">{ak_data['role_ru']}</small><br>
            <b style="font-size:1.7em; color:white;">{ak_data['planet_full']}</b><br>
            <code style="font-size:1.1em; color:#778DA9;">{ak_data['sign_full']} {ak_data['degree']}</code><br>
            <div style="margin-top:10px; font-size:1em; color:#A9D6E5;">{ak_data['nak_full']} | {ak_data['nak_sym']}</div>
        </div>""", unsafe_allow_html=True)

    with c_amk:
        st.markdown(f"""<div style="background:#0D1B2A; padding:20px; border-radius:10px; border-top: 4px solid #778DA9; min-height:170px;">
            <small style="color:#778DA9; font-weight:bold;">{amk_data['role_ru']}</small><br>
            <b style="font-size:1.7em; color:white;">{amk_data['planet_full']}</b><br>
            <code style="font-size:1.1em; color:#778DA9;">{amk_data['sign_full']} {amk_data['degree']}</code><br>
            <div style="margin-top:10px; font-size:1em; color:#A9D6E5;">{amk_data['nak_full']} | {amk_data['nak_sym']}</div>
        </div>""", unsafe_allow_html=True)

    # Шкала прогресса
    ak_name_now = df.iloc[0]['Planet']
    s_t, e_t = now_utc, now_utc
    for m in range(0, 2880, 10):
        t_c = ts.utc((now_utc - timedelta(minutes=m)).year, (now_utc - timedelta(minutes=m)).month, (now_utc - timedelta(minutes=m)).day, (now_utc - timedelta(minutes=m)).hour, (now_utc - timedelta(minutes=m)).minute)
        if get_planet_data(t_c)[0].iloc[0]['Planet'] != ak_name_now: s_t = now_utc - timedelta(minutes=m); break
    for m in range(0, 2880, 10):
        t_c = ts.utc((now_utc + timedelta(minutes=m)).year, (now_utc + timedelta(minutes=m)).month, (now_utc + timedelta(minutes=m)).day, (now_utc + timedelta(minutes=m)).hour, (now_utc + timedelta(minutes=m)).minute)
        if get_planet_data(t_c)[0].iloc[0]['Planet'] != ak_name_now: e_t = now_utc + timedelta(minutes=m); break
    
    total = (e_t - s_t).total_seconds()
    prog = min(max((now_utc - s_t).total_seconds() / total, 0.0), 1.0) if total > 0 else 0.5
    st.progress(prog)
    st.caption(f"Старт: {(s_t + timedelta(hours=3)).strftime('%d.%m %H:%M')} | Финиш: {(e_t + timedelta(hours=3)).strftime('%d.%m %H:%M')}")

    st.markdown("---")
    
# --- 4. ПОЛНЫЙ СПИСОК КАРАК (БЕЗ ДУБЛЕЙ) ---
    with st.expander("📊 ПОЛНЫЙ СПИСОК ЧАРА-КАРАК", expanded=True):
        rows_html = ""
        for i, row in df.iterrows():
            d = get_extended_info(row)
            
            rows_html += f"""
            <tr style="border-bottom: 1px solid #1E293B;">
                <td style="padding:14px; color:#94A3B8; font-weight:600; font-size:0.9em; white-space:nowrap;">{d['role_ru']}</td>
                <td style="padding:14px; color:#FFFFFF; font-size:1.1em; white-space:nowrap;">{d['planet_full']}</td>
                <td style="padding:14px; color:#E2E8F0; white-space:nowrap;">
                    <span style="margin-right:8px; opacity:0.9;">{d['sign_icon']}</span>{d['sign_only']}
                </td>
                <td style="padding:14px; font-family:'Roboto Mono', monospace; color:#38BDF8; font-weight:bold; white-space:nowrap;">{d['degree']}</td>
                <td style="padding:14px; color:#F1F5F9; white-space:nowrap;">{d['nak_full']}</td>
                <td style="padding:14px; color:#94A3B8; font-style:italic; font-size:0.95em; white-space:nowrap;">{d['nak_sym']}</td>
            </tr>"""

        st.markdown(f"""
        <div style="overflow-x:auto; background-color: #0F172A; border-radius: 12px; border: 1px solid #1E293B; padding: 5px;">
            <table style="width:100%; border-collapse: collapse; font-family: 'Inter', sans-serif; text-align: left;">
                <thead>
                    <tr style="background-color: #1E293B; border-bottom: 2px solid #334155;">
                        <th style="padding:16px; color:#64748B; font-size:0.85em; text-transform:uppercase;">Роль</th>
                        <th style="padding:16px; color:#64748B; font-size:0.85em; text-transform:uppercase;">Планета</th>
                        <th style="padding:16px; color:#64748B; font-size:0.85em; text-transform:uppercase;">Знак</th>
                        <th style="padding:16px; color:#64748B; font-size:0.85em; text-transform:uppercase;">Градус</th>
                        <th style="padding:16px; color:#64748B; font-size:0.85em; text-transform:uppercase;">Накшатра</th>
                        <th style="padding:16px; color:#64748B; font-size:0.85em; text-transform:uppercase;">Символ</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>
        </div>
        """, unsafe_allow_html=True)
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
