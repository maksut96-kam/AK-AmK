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
Z_ICONS = {"Овен": "♈ Овен", "Телец": "♉ Телец", "Близнецы": "♊ Близн", "Рак": "♋ Рак", "Лев": "♌ Лев", "Дева": "♍ Дева", "Весы": "♎ Весы", "Скорпион": "♏ Скорп", "Стрелец": "♐ Стрел", "Козерог": "♑ Козег", "Водолей": "♒ Водол", "Рыбы": "♓ Рыбы"}

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
            unique.append(s)
            seen.add(s["Дата"])
    return unique[:5]

def get_full_info(row):
    sign = ZODIAC_SIGNS[int(row['Lon']/30)]
    return f"{P_ICONS.get(row['Planet'], row['Planet'])} | {Z_ICONS.get(sign, sign)} {row['Deg']:.2f}°"

# ============================================================
# ⛔ БЛОК 3: ПОЛНАЯ СБОРКА (БЕЗ ОШИБОК)
# ============================================================
import base64
import os
import streamlit as st
import streamlit.components.v1 as components

def get_base64_img(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

logo_data = get_base64_img("logo.png")

# 1. СТИЛИ (CSS)
st.markdown(f"""
<style>
    /* Шапка: Лого + Текст */
    .header-wrapper {{
        display: flex;
        align-items: center;
        margin-bottom: 20px;
    }}
    .fish-logo {{
        width: 60px; height: 60px;
        background-image: url('data:image/png;base64,{logo_data}');
        background-size: contain; background-repeat: no-repeat;
        margin-right: 20px;
    }}
    .main-title {{
        font-family: 'Lexend', sans-serif; font-weight: 800; font-size: 2.8em;
        text-transform: uppercase; color: white; margin: 0;
    }}

    /* Баннер и Полет планет */
    .space-banner {{
        position: relative; width: 100%; height: 300px;
        border-radius: 20px; overflow: hidden;
        background: black; border: 1px solid rgba(255,255,255,0.1);
    }}
    .planet {{
        position: absolute; top: 0; left: 0; right: 0; bottom: 0;
        transform: scale(0); opacity: 0;
        animation: fly 3s infinite linear;
    }}
    .p1 {{ background-image: radial-gradient(circle, #415A77 8px, transparent 15px); background-size: 400px 400px; animation-duration: 4s; }}
    .p2 {{ background-image: radial-gradient(circle, #778DA9 4px, transparent 10px); background-size: 300px 300px; animation-duration: 2.5s; animation-delay: 1s; }}
    
    @keyframes fly {{
        0% {{ transform: scale(0.1); opacity: 0; }}
        50% {{ opacity: 1; }}
        100% {{ transform: scale(2.5); opacity: 0; }}
    }}

    /* Часы (Стекляшка) */
    .clock-box {{
        position: absolute; bottom: 20px; right: 20px;
        background: rgba(13, 27, 42, 0.7); backdrop-filter: blur(10px);
        padding: 10px 20px; border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.1); z-index: 99;
    }}
</style>

<div class="header-wrapper">
    <div class="fish-logo"></div>
    <div>
        <h1 class="main-title">Julia's Assistant</h1>
        <div style="color: #778DA9; letter-spacing: 5px; font-size: 0.9em;">ASTRO COORDINATION CENTER</div>
    </div>
</div>

<div class="space-banner">
    <div class="planet p1"></div>
    <div class="planet p2"></div>
    <div class="clock-box">
        <span id="live-clock" style="color: white; font-weight: bold; font-family: monospace; font-size: 1.5em;">00:00:00</span>
        <div style="color: #778DA9; font-size: 0.7em; text-transform: uppercase;">Sochi Time</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 2. ОЖИВЛЕНИЕ ЧАСОВ (JS)
components.html("""
    <script>
    function tick() {
        let d = new Date();
        let utc = d.getTime() + (d.getTimezoneOffset() * 60000);
        let sochi = new Date(utc + (3600000 * 3));
        let s = sochi.toTimeString().split(' ')[0];
        const el = window.parent.document.getElementById('live-clock');
        if (el) el.innerHTML = s;
    }
    setInterval(tick, 1000); tick();
    </script>
""", height=0)
# ============================================================
# ⛔ БЛОК 4: ОПЕРАТИВНЫЙ МОНИТОРИНГ (ТАБЫ)
# ============================================================
tab1, tab2 = st.tabs(["📊 Прямой эфир", "📅 Высокоточный Планировщик"])

with tab1:
    now_utc = datetime.utcnow()
    t_now = ts.utc(now_utc.year, now_utc.month, now_utc.day, now_utc.hour, now_utc.minute, now_utc.second)
    df, ra_lon, ra_deg = get_planet_data(t_now)
    tithi, l_status, l_icon = get_lunar_data(t_now)

        # --- ТАБЛИЦА КАРАК ---
    st.subheader("📊 Таблица Чара-карак")
    df_v = df.copy()
    df_v['Знак'] = df_v['Lon'].apply(lambda x: Z_ICONS[ZODIAC_SIGNS[int(x/30)]])
    df_v['Накшатра'] = df_v['Lon'].apply(lambda x: f"{NAKSHATRAS[int(x/(360/27))%27]} ({NAK_LORDS[int(x/(360/27))%27]})")
    df_v['Градус'] = df_v['Deg'].apply(lambda x: f"{x:.4f}°")
    st.dataframe(df_v[['Role', 'Planet', 'Знак', 'Накшатра', 'Градус']], use_container_width=True, hide_index=True)

    st.divider()

       # --- МОДУЛЬ ЛУНЫ (ВОССТАНОВЛЕНО) ---
    st.markdown(f"### {l_icon} Лунный цикл: {tithi} сутки")
    st.info(f"Текущая фаза: **{l_status}**")

    st.markdown("---")
    
    # --- МОДУЛЬ РАХУ (ПОЛНЫЙ) ---
    if ra_deg < 2 or ra_deg > 28:
        label, color, desc = "🔴 КРИТИЧЕСКИЙ ХАОС", "#FF4B4B", "Зона Ганданты. Рынок крайне иррационален."
    elif ra_deg < 5 or ra_deg > 25:
        label, color, desc = "🟡 ПОВЫШЕННЫЙ РИСК", "#FFA500", "Эмоциональные качели. Возможны сквизы."
    else:
        label, color, desc = "🟢 ТЕХНИЧНЫЙ РЫНОК", "#00C853", "Чистая зона. Теханализ в норме."

    st.markdown(f"""<div style="background:{color}22; border-left:5px solid {color}; padding:15px; border-radius:10px; border:1px solid {color}44;">
        <h3 style="margin:0; color:{color};">🐲 Монитор Раху: {label}</h3>
        <p style="margin:5px 0;">{desc} (Текущий градус: <b>{ra_deg:.2f}°</b>)</p></div>""", unsafe_allow_html=True)
    
    st.subheader("📡 Радар аномалий XAUUSD")
    c_r1, c_r2 = st.columns([1, 2])
    with c_r1:
        score = 100 - (ra_deg*5) if ra_deg < 10 else (ra_deg-20)*10 if ra_deg > 20 else 5
        st.write("**Давление Раху:**")
        st.progress(min(max(int(score), 5), 100))
    with c_r2:
        storms = get_xau_storms(now_utc)
        if storms:
            for s in storms:
                st.warning(f"**{s['Дата']}** — {s['Тип']} (Угол {s['Угол']})")
        else:
            st.success("✅ Критических помех для золота не обнаружено.")

    st.markdown("---")

    # --- МОНИТОРИНГ РОТАЦИЙ (ВОССТАНОВЛЕНО) ---
    st.subheader("🔄 Мониторинг ротаций")
    ak_now, amk_now = df.iloc[0]['Planet'], df.iloc[1]['Planet']
    
    c_m1, c_m2 = st.columns(2)
    c_m1.metric("💎 Текущая АК", get_full_info(df.iloc[0]))
    c_m2.metric("🥈 Текущая AmK", get_full_info(df.iloc[1]))

    cols = st.columns(2)
    settings = [(-1, "⬅️ Предыдущая смена", "#415A77"), (1, "➡️ Следующая смена", "#778DA9")]
    for idx, (direct, label_rot, color_rot) in enumerate(settings):
        with cols[idx]:
            st.markdown(f"<h4 style='color:{color_rot}; border-bottom:1px solid #eee;'>{label_rot}</h4>", unsafe_allow_html=True)
            for m in range(10, 2880, 10):
                target = now_utc + timedelta(minutes=m*direct)
                t_t = ts.utc(target.year, target.month, target.day, target.hour, target.minute)
                df_t, _, _ = get_planet_data(t_t)
                if df_t.iloc[0]['Planet'] != ak_now or df_t.iloc[1]['Planet'] != amk_now:
                    st.success(f"📅 {(target + timedelta(hours=3)).strftime('%d.%m %H:%M')}")
                    st.caption(f"АК: {get_full_info(df_t.iloc[0])}\n\nAmK: {get_full_info(df_t.iloc[1])}")
                    break

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
