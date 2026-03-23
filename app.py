import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd
import streamlit.components.v1 as components
import math
import os

# 1. Системные настройки
st.set_page_config(page_title="Julia Assistant Astro", layout="wide")

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
    current_ayan = get_dynamic_ayanamsa(t)
    earth = eph['earth']
    planets_objects = {'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 'Mercury': eph['mercury'], 'Jupiter': eph['jupiter_barycenter'], 'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']}
    res = []
    for name, obj in planets_objects.items():
        lon = (earth.at(t).observe(obj).ecliptic_latlon()[1].degrees - current_ayan) % 360
        res.append({'Planet': name, 'Lon': lon, 'Deg': lon % 30})
    
    lat, lon, dist = earth.at(t).observe(eph['moon']).ecliptic_latlon()
    ra_lon = (lon.degrees - current_ayan + 180) % 360 
    res.append({'Planet': 'Rahu', 'Lon': ra_lon, 'Deg': 30 - (ra_lon % 30)}) 
    
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    roles = ['AK', 'AmK', 'BK', 'MK', 'PiK', 'PK', 'GK', 'DK']
    df['Role'] = roles[:len(df)]
    ketu_lon = (ra_lon + 180) % 360
    df = pd.concat([df, pd.DataFrame([{'Planet': 'Ketu', 'Lon': ketu_lon, 'Deg': ketu_lon % 30, 'Role': '-'}])], ignore_index=True)
    return df, current_ayan

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

# --- ИНТЕРФЕЙС ---

col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
with col_l2:
    if os.path.exists("logo.png"): 
        st.image("logo.png", use_container_width=True)

# ТЕМНЫЙ ДИНАМИЧЕСКИЙ ГРАДИЕНТ
st.markdown("""
<style>
    @keyframes dark-glow { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }
    .julia-title {
        text-align: center; margin-top: -10px; margin-bottom: 25px; font-weight: 800; font-size: 3.2em;
        background: linear-gradient(270deg, #0D1B2A, #1B263B, #415A77, #0D1B2A);
        background-size: 400% 400%; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        animation: dark-glow 10s ease infinite;
    }
</style>
<h1 class="julia-title">Julia Assistant Astro Coordination Center</h1>
""", unsafe_allow_html=True)

components.html("""
    <div style="background: linear-gradient(90deg, #050510, #0a0a20); padding:15px; border-radius:15px; text-align:center; font-family: sans-serif; border: 1px solid #1B263B;">
        <h2 id="clock" style="margin:0; color:#415A77; letter-spacing: 2px;">Загрузка...</h2>
        <p style="margin:0; color:#778DA9; font-size: 0.8em; text-transform: uppercase;">Sochi Astro-Coordination Time (UTC+3)</p>
    </div>
    <script>
        function updateClock() {
            let d = new Date(); let utc = d.getTime() + (d.getTimezoneOffset() * 60000);
            let sochi = new Date(utc + (3600000 * 3));
            document.getElementById('clock').innerHTML = sochi.toLocaleTimeString('ru-RU');
        }
        setInterval(updateClock, 1000); updateClock();
    </script>
""", height=110)

tab1, tab2 = st.tabs(["📊 Прямой эфир", "📅 План на неделю"])

with tab1:
    # 2. КНОПКА ОБНОВЛЕНИЯ И ЖИВОЕ ВРЕМЯ
    col_upd1, col_upd2 = st.columns([5, 1])
    with col_upd2:
        btn_refresh = st.button("🔄 Обновить")
    
    now_utc = datetime.utcnow()
    sochi_now = now_utc + timedelta(hours=3)
    
    t_now = ts.utc(now_utc.year, now_utc.month, now_utc.day, now_utc.hour, now_utc.minute, now_utc.second)
    df, ayan_val = get_planet_data(t_now)
    tithi, l_status, l_icon = get_lunar_info(t_now)
    delta_t = t_now.delta_t

    st.markdown(f"**📍 Данные построены на:** `{sochi_now.strftime('%d.%m.%Y %H:%M:%S')}` (Сочи)")

    st.markdown(f"""
    <div style="background: #0D1B2A; border-left: 5px solid #1B263B; padding: 15px; border-radius: 10px; color: #E0E1DD; margin-bottom: 15px;">
        <h3 style="margin:0; color: #778DA9;">{l_icon} Лунный цикл</h3>
        <p style="margin:5px 0;"><b>Титхи:</b> {tithi} сутки | <b>Статус:</b> {l_status}</p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander(f"🔮 Айанамша Лахири: {format_deg_to_min(ayan_val)}", expanded=True):
        st.write(f"**Значение ΔT (Delta T):** {delta_t:.4f} сек.")
        st.caption("Шкала TT (Terrestrial Time) используется для исключения погрешностей вращения Земли при расчете прецессии Лахири.")
    
    # Таблица прямого эфира
    df_v = df.copy()
    df_v['Знак'] = df_v['Lon'].apply(lambda x: Z_ICONS[ZODIAC_SIGNS[int(x/30)]])
    df_v['Накшатра'] = df_v['Lon'].apply(lambda x: f"{NAKSHATRAS[int(x/(360/27))%27]} ({NAK_LORDS[int(x/(360/27))%27]})")
    df_v['Градус'] = df_v['Deg'].apply(lambda x: f"{x:.4f}°")
    df_v.index = range(1, len(df_v) + 1)
    st.table(df_v[['Role', 'Planet', 'Знак', 'Накшатра', 'Градус']])

    st.markdown("---")
    
    # 1. ОФОРМЛЕНИЕ МОНИТОРИНГА РОТАЦИЙ
    st.subheader("🔄 Мониторинг ротаций (Текущие и Смены)")
    
    # Визуализация текущих АК и AmK
    c_cur1, c_cur2 = st.columns(2)
    with c_cur1:
        st.metric("💎 Текущая АК (Атма-карака)", get_full_info(df.iloc[0]))
    with c_cur2:
        st.metric("🥈 Текущая AmK (Аматья-карака)", get_full_info(df.iloc[1]))
    
    st.write("") # Отступ
    
    ak_now, amk_now = df.iloc[0]['Planet'], df.iloc[1]['Planet']
    c1, c2 = st.columns(2)
    for col, direct, label, color in zip([c1, c2], [-1, 1], ["⬅️ Предыдущая смена", "➡️ Следующая смена"], ["#415A77", "#778DA9"]):
        with col:
            st.markdown(f"<h4 style='color:{color};'>{label}</h4>", unsafe_allow_html=True)
            found = False
            for m in range(10, 2880, 10):
                target = now_utc + timedelta(minutes=m*direct)
                t_t = ts.utc(target.year, target.month, target.day, target.hour, target.minute)
                df_t, _ = get_planet_data(t_t)
                if df_t.iloc[0]['Planet'] != ak_now or df_t.iloc[1]['Planet'] != amk_now:
                    st.success(f"📅 {(target + timedelta(hours=3)).strftime('%d.%m %H:%M')}")
                    st.write(f"**АК:** {get_full_info(df_t.iloc[0])}")
                    st.write(f"**AmK:** {get_full_info(df_t.iloc[1])}")
                    found = True
                    break
            if not found: st.info("В ближайшие 48ч смен не найдено")

with tab2:
    st.header("Таймлайн на неделю")
    if st.button('🗓 Сгенерировать план'):
        ref = datetime.utcnow() + timedelta(hours=3)
        start = ref - timedelta(days=ref.weekday()); start = start.replace(hour=0, minute=0)
        events, last_pair = [], ""
        for h in range(168):
            ct = start + timedelta(hours=h)
            t_w = ts.utc(ct.year, ct.month, ct.day, ct.hour-3, 0)
            df_w, _ = get_planet_data(t_w)
            pair = f"{df_w.iloc[0]['Planet']}/{df_w.iloc[1]['Planet']}"
            if pair != last_pair:
                events.append({"Дата": ct.strftime("%d.%m %H:00"), "АК": get_full_info(df_w.iloc[0]), "AmK": get_full_info(df_w.iloc[1])})
                last_pair = pair
        df_p = pd.DataFrame(events)
        df_p.index = range(1, len(df_p) + 1)
        st.table(df_p)
