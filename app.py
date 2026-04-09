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
# ⛔ БЛОК 3: ЛОГОТИП, ВЕРХНИЙ ЗАГОЛОВОК И ДИНАМИЧЕСКИЙ БАННЕР (ФИНАЛ)
# ============================================================
import base64
import os

# Функция для загрузки изображений (оставляем без изменений)
def get_base64_img(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

# Загружаем логотип с рыбками
logo_data = get_base64_img("logo.png")

# --- 1. ВЕРХНЯЯ ПАНЕЛЬ (ЛОГО + ЗАГОЛОВОК) ---
# Эта часть находится НАД баннером, на чистом фоне.
st.markdown(f"""
<style>
    /* Контейнер для всей верхней панели */
    .top-panel-final {{
        display: flex;
        align-items: center;
        justify-content: center; /* Центрируем заголовок */
        margin-top: -10px; /* Поднимаем повыше */
        margin-bottom: 25px; /* Отступ до баннера */
        position: relative;
    }}

    /* СТИЛЬ ЛОГОТИПА (Рыбки) - СЛЕВА */
    .logo-final {{
        width: 100px; /* Размер логотипа */
        height: 100px;
        background-image: url('data:image/png;base64,{logo_data}');
        background-size: contain;
        background-repeat: no-repeat;
        background-position: center;
        position: absolute;
        left: 20px; /* Отступ от левого края */
        filter: brightness(0.9) contrast(1.1); /* Немного ярче */
    }}

    /* СТИЛЬ ЗАГОЛОВОКА (Julia's Assistant) - ПО ЦЕНТРУ */
    .title-final-clean {{
        text-align: center;
        margin: 0;
    }}

    .title-main-clean {{
        font-family: 'Lexend', sans-serif;
        font-weight: 800;
        font-size: 3.2em; /* Крупный размер */
        letter-spacing: 5px;
        text-transform: uppercase;
        color: #FFFFFF !important; /* Белый для темной темы */
        text-shadow: 0 0 15px rgba(65, 90, 119, 0.7); /* Минимальное свечение */
        margin: 0;
    }}

    .subtitle-clean {{
        color: #778DA9; 
        letter-spacing: 12px; 
        margin-top: 5px; 
        font-weight: bold; 
        font-size: 1.1em; 
        text-transform: uppercase;
        display: block;
    }}
</style>

<div class="top-panel-final">
    <div class="logo-final"></div>
    
    <div class="title-final-clean">
        <h1 class="title-main-clean">Julia's Assistant</h1>
        <span class="subtitle-clean">Astro Coordination Center</span>
    </div>
</div>
""", unsafe_allow_html=True)


# --- 2. ДИНАМИЧЕСКИЙ БАННЕР (ВЫЛЕТАЮЩИЕ ПЛАНЕТЫ И ЗВЕЗДЫ) ---
# Эта часть находится НИЖЕ заголовка. Внутри баннера больше НЕТ логотипа с рыбками.
st.markdown(f"""
<style>
    /* Основной контейнер баннера "Иллюминатор" */
    .viewport-final-banner {{
        position: relative;
        width: 100%;
        height: 300px; /* Высота баннера */
        border-radius: 20px;
        overflow: hidden;
        background: #000; /* Черный космос */
        border: 2px solid rgba(65, 90, 119, 0.4);
        box-shadow: 0 10px 50px rgba(0,0,0,0.9);
        margin-bottom: 30px;
    }}

    /* СЛОИ ПАРАЛЛАКСА (Анимация из центра на зрителя) */
    .parallax-layer-final {{
        position: absolute;
        top: 0; left: 0; width: 100%; height: 100%;
        z-index: 2;
        transform: scale(0); /* Изначально скрыты */
        opacity: 0;
        animation: warp-drive 2s infinite linear;
    }}

    /* Слой 1: ДАЛЬНИЙ (Планеты-частицы вылетают медленно, маленькие) */
    .warp-distant-final {{
        animation-duration: 2s;
        animation-delay: 0s;
        background-image: 
            radial-gradient(4px 4px at 50px 50px, #aabbee, rgba(0,0,0,0)), /* Синяя планета */
            radial-gradient(3px 3px at 150px 100px, #eeddaa, rgba(0,0,0,0)), /* Золотая планета */
            radial-gradient(2px 2px at 250px 200px, #ffffff, rgba(0,0,0,0)); /* Дальняя звезда */
        background-repeat: repeat;
        background-size: 400px 400px;
        opacity: 0.3;
    }}

    /* Слой 2: СРЕДНИЙ (Средняя скорость вылета) */
    .warp-middle-final {{
        animation-duration: 1.5s;
        animation-delay: 0.5s;
        background-image: 
            radial-gradient(6px 6px at 100px 150px, #ccddff, rgba(0,0,0,0)), /* Крупная синяя планета */
            radial-gradient(5px 5px at 200px 50px, #ffdcaa, rgba(0,0,0,0)); /* Крупная золотая планета */
        background-repeat: repeat;
        background-size: 300px 300px;
        opacity: 0.6;
    }}

    /* Слой 3: БЛИЖНИЙ (БЫСТРЫЙ, КРУПНЫЙ) */
    .warp-close-final {{
        animation-duration: 1.2s;
        animation-delay: 1s;
        background-image: 
            radial-gradient(10px 10px at 50px 50px, #ffffff, rgba(0,0,0,0)), /* Ближняя крупная звезда */
            radial-gradient(8px 8px at 150px 150px, #415A77, rgba(0,0,0,0)); /* Ближняя планета */
        background-repeat: repeat;
        background-size: 200px 200px;
        opacity: 0.8;
    }}

    @keyframes warp-drive {{
        0% {{ transform: scale(0.2); opacity: 0; }}
        20% {{ opacity: 1; }}
        80% {{ opacity: 1; }}
        100% {{ transform: scale(2.5); opacity: 0; }} /* Вылетают за экран */
    }}

    /* ЧАСЫ (Glassmorphism стиль внутри баннера) */
    .clock-glass-final {{
        position: absolute;
        bottom: 20px; right: 20px;
        z-index: 10;
        background: rgba(13, 27, 42, 0.85);
        padding: 8px 18px;
        border-radius: 15px;
        border: 1px solid rgba(255,255,255,0.2);
        backdrop-filter: blur(8px);
    }}
</style>

<div class="viewport-final-banner">
    <div class="parallax-layer-final warp-distant-final"></div>
    <div class="parallax-layer-final warp-middle-final"></div>
    <div class="parallax-layer-final warp-close-final"></div>

    <div class="clock-glass-final">
        <span id="mini-clock-target" style="color: white; font-weight: bold; font-family: 'Courier New', monospace; font-size: 1.4em;">00:00:00</span>
        <div style="color: #415A77; font-size: 0.7em; text-transform: uppercase; letter-spacing: 2px;">Sochi Time</div>
    </div>
</div>
""", unsafe_allow_html=True)


# --- 3. СКРИПТ ЧАСОВ (С ПРЯМЫМ ДОСТУПОМ К ЭЛЕМЕНТУ) ---
import streamlit.components.v1 as components
components.html("""
    <script>
    function update() {
        let d = new Date();
        let utc = d.getTime() + (d.getTimezoneOffset() * 60000);
        let sochi = new Date(utc + (3600000 * 3));
        let t = sochi.toLocaleTimeString('ru-RU');
        // Ищем элемент в родительском окне
        const clock = window.parent.document.getElementById('mini-clock-target');
        if (clock) clock.innerHTML = t;
    }
    setInterval(update, 1000);
    update();
    </script>
""", height=0)

st.markdown("---")
# ============================================================
# ⛔ БЛОК 4: ОПЕРАТИВНЫЙ МОНИТОРИНГ (ТАБЫ)
# ============================================================
tab1, tab2 = st.tabs(["📊 Прямой эфир", "📅 Высокоточный Планировщик"])

with tab1:
    now_utc = datetime.utcnow()
    t_now = ts.utc(now_utc.year, now_utc.month, now_utc.day, now_utc.hour, now_utc.minute, now_utc.second)
    df, ra_lon, ra_deg = get_planet_data(t_now)
    tithi, l_status, l_icon = get_lunar_data(t_now)
    
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

    # --- МОДУЛЬ ЛУНЫ (ВОССТАНОВЛЕНО) ---
    st.markdown(f"### {l_icon} Лунный цикл: {tithi} сутки")
    st.info(f"Текущая фаза: **{l_status}**")

    st.markdown("---")
    
    # --- ТАБЛИЦА КАРАК ---
    st.subheader("📊 Таблица Чара-карак")
    df_v = df.copy()
    df_v['Знак'] = df_v['Lon'].apply(lambda x: Z_ICONS[ZODIAC_SIGNS[int(x/30)]])
    df_v['Накшатра'] = df_v['Lon'].apply(lambda x: f"{NAKSHATRAS[int(x/(360/27))%27]} ({NAK_LORDS[int(x/(360/27))%27]})")
    df_v['Градус'] = df_v['Deg'].apply(lambda x: f"{x:.4f}°")
    st.dataframe(df_v[['Role', 'Planet', 'Знак', 'Накшатра', 'Градус']], use_container_width=True, hide_index=True)

    st.divider()

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
