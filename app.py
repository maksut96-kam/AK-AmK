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
# ⛔ БЛОК 3: ГИПЕРПРОСТРАНСТВЕННАЯ ПАНЕЛЬ (MOVING SPACE SHIELD)
# ============================================================

# 1. СНАЧАЛА ОПРЕДЕЛЯЕМ ФУНКЦИЮ (чтобы не было NameError)
import base64
import os

def get_base64_img(path):
    if os.path.exists(path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

# 2. ТЕПЕРЬ ВЫЗЫВАЕМ ЕЁ
logo_data = get_base64_img("logo.png")

# 3. ДАЛЬШЕ ИДЕТ ВЕСЬ ОСТАЛЬНОЙ CSS (st.markdown)
st.markdown("""
<style>
    /* Основной контейнер "Иллюминатор" */
    .space-port {
        position: relative;
        width: 100%;
        height: 300px;
        border-radius: 20px;
        overflow: hidden;
        background-color: #050505;
        margin-bottom: 30px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.8);
        border: 2px solid rgba(65, 90, 119, 0.3);
    }

    /* СЛОЙ 1: Неподвижный логотип (как подложка) */
    .logo-static {
        position: absolute;
        width: 100%;
        height: 100%;
        background-image: url('data:image/png;base64,{logo_base64}'); 
        background-size: cover;
        background-position: center;
        filter: brightness(0.5) contrast(1.1); /* Затемняем, чтобы текст читался */
        z-index: 1;
    }

    /* СЛОЙ 2: Быстро движущиеся частицы (эффект полета) */
    .space-warp {
        position: absolute;
        width: 100%;
        height: 100%;
        background-image: 
            radial-gradient(white, rgba(255,255,255,.2) 2px, transparent 3px),
            radial-gradient(white, rgba(255,255,255,.15) 1px, transparent 2px),
            radial-gradient(white, rgba(255,255,255,.1) 2px, transparent 3px);
        background-size: 550px 550px, 350px 350px, 250px 250px;
        background-position: 0 0, 40px 60px, 130px 270px;
        z-index: 2;
        /* АНИМАЦИЯ ПОЛЕТА: Сдвиг фона по вертикали */
        animation: space-fly 1.5s linear infinite; /* 1.5s - быстро */
        opacity: 0.8;
    }

    @keyframes space-fly {
        from { background-position: 0 0, 40px 60px, 130px 270px; }
        to { background-position: 0 100%, 40px 100%, 130px 100%; }
    }

    /* СЛОЙ 3: Заголовок сверху */
    .title-overlay-art {
        position: absolute;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%); /* Центрируем */
        width: 90%;
        text-align: center;
        z-index: 3;
    }

    .julia-title-art {
        font-family: 'Lexend', sans-serif;
        font-weight: 800;
        font-size: 3.8em;
        letter-spacing: 6px;
        text-transform: uppercase;
        color: white;
        text-shadow: 0 0 15px rgba(255,255,255,0.6), 0 0 30px rgba(65, 90, 119, 0.8);
        margin: 0;
    }

    /* Мини-часы (как в арте) */
    .clock-overlay-art {
        position: absolute;
        bottom: 10px;
        right: 20px;
        z-index: 3;
        background: rgba(13, 27, 42, 0.7);
        padding: 5px 15px;
        border-radius: 20px;
        border: 1px solid rgba(255,255,255,0.1);
        backdrop-filter: blur(5px);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# Подготовка изображения для CSS (оставляем функцию из прошлого ответа)
# get_base64_img("logo.png") должна быть определена выше

logo_data = get_base64_img("logo.png")

# 2. Рендеринг трехслойной конструкции
st.markdown(f"""
    <div class="space-port">
        <div class="logo-static" style="background-image: url('data:image/png;base64,{logo_data}');"></div>
        <div class="space-warp"></div>
        <div class="title-overlay-art">
            <h1 class="julia-title-art">Julia Assistant</h1>
            <p style="color: #778DA9; letter-spacing: 9px; margin-top: -10px; font-size: 1.1em;">ASTRO COORDINATION CENTER</p>
        </div>
        <div class="clock-overlay-art">
            <span id="mini-clock-art" style="color: white; font-weight: bold; font-family: monospace; font-size: 1.3em;">00:00:00</span>
            <div style="color: #415A77; font-size: 0.7em; text-transform: uppercase;">SOCHI LIVE</div>
        </div>
    </div>
""", unsafe_allow_html=True)

# 3. Скрипт для часов (встраиваем отдельно, ID обновлен)
components.html("""
    <script>
        function updateClock() {
            let d = new Date();
            let utc = d.getTime() + (d.getTimezoneOffset() * 60000);
            let sochi = new Date(utc + (3600000 * 3));
            let h = String(sochi.getHours()).padStart(2, '0');
            let m = String(sochi.getMinutes()).padStart(2, '0');
            let s = String(sochi.getSeconds()).padStart(2, '0');
            // Обновляем часы только в родительском окне
            if (window.parent.document.getElementById('mini-clock-art')) {
                window.parent.document.getElementById('mini-clock-art').innerHTML = h + ":" + m + ":" + s;
            }
        }
        setInterval(updateClock, 1000);
        updateClock();
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
