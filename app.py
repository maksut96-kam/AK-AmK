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
    delta_t = t_now.delta_t

    st.markdown(f"**📍 Расчет на момент:** `{sochi_now.strftime('%d.%m.%Y %H:%M:%S')}` (Сочи)")

    st.markdown(f"""
    <div style="background: #f8f9fa; border-left: 5px solid #1B263B; padding: 15px; border-radius: 10px; color: #333; margin-bottom: 15px; border: 1px solid #dee2e6;">
        <h3 style="margin:0; color: #1B263B;">{l_icon} Лунный цикл</h3>
        <p style="margin:5px 0;"><b>Титхи:</b> {tithi} сутки | <b>Статус:</b> {l_status}</p>
    </div>
    """, unsafe_allow_html=True)

    with st.expander(f"🔮 Айанамша Лахири: {format_deg_to_min(ayan_val)} (Служебная информация)", expanded=False):
        st.write(f"**Текущее значение ΔT (Delta T):** {delta_t:.4f} сек.")
        st.markdown("""
        ---
        ### 1. Что это физически?
        **TT (Terrestrial Time)** — это идеализированное, равномерное время. Оно не зависит от капризов вращения планеты и используется как основной аргумент в математических эфемеридах.

        ### 2. Почему это важно для Лахири?
        Айанамша — это угол между точкой весеннего равноденствия и точкой начала неподвижного зодиака. Он меняется из-за прецессии. Формула:  
        $$23.856235 + (2.30142 \cdot T) + (0.000139 \cdot T^2)$$  
        Переменная **$T$** — это столетия с эпохи J2000.0. Для точности нам нужно значение **t.tt**, которое дает «чистую» шкалу без погрешностей вращения Земли.

        ### 3. Как это работает в твоем коде?
        Когда мы пишем `T = (t.tt - 2451545.0) / 36525.0`, мы используем «сверхточные космические часы».
        """)
    
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
    st.header("📅 Поиск точных периодов АК/AmK")
    st.write("Настройте временной интервал (точность расчета — 1 минута).")
    
    # Использование session_state для стабильности выбора
    if 'start_dt' not in st.session_state: st.session_state.start_dt = datetime.now()
    if 'end_dt' not in st.session_state: st.session_state.end_dt = datetime.now() + timedelta(days=3)

    col_date1, col_date2 = st.columns(2)
    with col_date1:
        s_d = st.date_input("С (дата)", st.session_state.start_dt.date(), key="s_date")
        s_t = st.time_input("С (время)", st.session_state.start_dt.time(), key="s_time", step=60)
    with col_date2:
        e_d = st.date_input("ПО (дата)", st.session_state.end_dt.date(), key="e_date")
        e_t = st.time_input("ПО (время)", st.session_state.end_dt.time(), key="e_time", step=60)

    dt_start_local = datetime.combine(s_d, s_t)
    dt_end_local = datetime.combine(e_d, e_t)

    if st.button('🚀 Рассчитать таблицу переходов'):
        if dt_start_local >= dt_end_local:
            st.error("Дата начала должна быть раньше даты конца.")
        else:
            with st.spinner('Сканируем небесную сферу поминутно...'):
                curr_utc = dt_start_local - timedelta(hours=3)
                end_utc = dt_end_local - timedelta(hours=3)
                events = []
                
                t_init = ts.utc(curr_utc.year, curr_utc.month, curr_utc.day, curr_utc.hour, curr_utc.minute)
                df_init, _ = get_planet_data(t_init)
                last_pair = f"{df_init.iloc[0]['Planet']}/{df_init.iloc[1]['Planet']}"
                
                events.append({"Время (Сочи)": dt_start_local.strftime("%d.%m.%Y %H:%M"), "АК": get_full_info(df_init.iloc[0]), "AmK": get_full_info(df_init.iloc[1]), "Событие": "Начало отсчета"})

                temp_utc = curr_utc
                while temp_utc < end_utc:
                    temp_utc += timedelta(minutes=1)
                    t_step = ts.utc(temp_utc.year, temp_utc.month, temp_utc.day, temp_utc.hour, temp_utc.minute)
                    df_step, _ = get_planet_data(t_step)
                    new_pair = f"{df_step.iloc[0]['Planet']}/{df_step.iloc[1]['Planet']}"
                    
                    if new_pair != last_pair:
                        events.append({"Время (Сочи)": (temp_utc + timedelta(hours=3)).strftime("%d.%m.%Y %H:%M"), "АК": get_full_info(df_step.iloc[0]), "AmK": get_full_info(df_step.iloc[1]), "Событие": "🔃 Смена ролей"})
                        last_pair = new_pair
                
                df_res = pd.DataFrame(events)
                df_res.index = range(1, len(df_res) + 1)
                st.table(df_res)
                st.download_button("💾 Скачать CSV", df_res.to_csv(index=False).encode('utf-8-sig'), "astro_schedule.csv")
