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
    
    # Считаем АК/AmK
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    df['Role'] = (['AK', 'AmK', 'BK', 'MK', 'PiK', 'GK', 'DK'] + ['-'] * 10)[:len(df)]
    
    # Считаем Раху и добавляем его ВНУТРЬ таблицы df
    ra_lon = (earth.at(t).observe(eph['moon']).ecliptic_latlon()[1].degrees - ayan + 180) % 360 
    ra_row = pd.DataFrame([{'Planet': 'Rahu', 'Lon': ra_lon, 'Deg': 30 - (ra_lon % 30), 'Role': '-'}])
    df = pd.concat([df, ra_row], ignore_index=True)
    
    # Возвращаем строго ДВА значения (таблицу и аянамшу)
    return df, ayan

def get_lunar_detailed_info(t):
    """Расширенная математика Луны для AmK"""
    earth = eph['earth']
    s_pos = earth.at(t).observe(eph['sun']).ecliptic_latlon()
    m_pos = earth.at(t).observe(eph['moon']).ecliptic_latlon()
    
    s_lon = s_pos[1].degrees
    m_lon = m_pos[1].degrees
    
    # 1. Титхи и освещенность
    diff = (m_lon - s_lon) % 360
    tithi_num = math.ceil(diff / 12) or 1
    illumination = (1 - math.cos(math.radians(diff))) / 2 * 100
    
    # 2. Время до сизигий (скорость ~0.508 град/час)
    dist_to_full = (180 - diff) % 360
    dist_to_new = (360 - diff) % 360
    h_to_full = dist_to_full / 0.508
    h_to_new = dist_to_new / 0.508
    
    # 3. Сидерические данные (Знак и Накшатра)
    ayan = get_dynamic_ayanamsa(t)
    lon_sid = (m_lon - ayan) % 360
    sign_idx = int(lon_sid / 30)
    nak_idx = int(lon_sid / (360/27)) % 27
    
    # 4. Фишка: Проверка на Ганданту (опасные стыки)
    gandanta = False
    deg_in_sign = lon_sid % 30
    if sign_idx in [3, 7, 11] and deg_in_sign > 27: gandanta = "Реактивная (конец воды)"
    if sign_idx in [0, 4, 8] and deg_in_sign < 3: gandanta = "Импульсивная (начало огня)"
    
    return {
        "tithi": tithi_num,
        "phase_icon": ["🌑","🌒","🌓","🌔","🌕","🌖","🌗","🌘"][int(((diff + 22.5) % 360) / 45)],
        "illum": illumination,
        "to_full": h_to_full,
        "to_new": h_to_new,
        "sign": ZODIAC_SIGNS[sign_idx],
        "nak": NAKSHATRAS[nak_idx],
        "nak_lord": NAK_LORDS[nak_idx],
        "is_waxing": diff < 180,
        "gandanta": gandanta
    }

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
    # 1. Сбор актуальных данных
    now_utc = datetime.utcnow()
    t_now = ts.utc(now_utc.year, now_utc.month, now_utc.day, now_utc.hour, now_utc.minute, now_utc.second)
    
    # ПРАВИЛЬНЫЙ ВЫЗОВ: принимаем ровно 2 значения
    df, ayan_val = get_planet_data(t_now)
    l = get_lunar_detailed_info(t_now) 

    def fmt_h(h):
        d = int(h // 24)
        hrs = int(h % 24)
        return f"{d}д {hrs}ч"

    # 2. ВИЗУАЛЬНЫЙ БЛОК: "ЛУННЫЙ АЛТАРЬ" (AmK Special)
    st.markdown(f"""
    <style>
        .moon-altar {{
            background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 100%);
            border-radius: 20px;
            padding: 25px;
            border: 1px solid rgba(119, 141, 169, 0.3);
            color: #e0e1dd;
            margin-bottom: 25px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.5);
        }}
        .moon-title {{ font-size: 1.8em; font-weight: 700; margin-bottom: 5px; }}
        .gandanta-alert {{
            background: rgba(230, 57, 70, 0.2);
            border: 1px solid #e63946;
            padding: 10px;
            border-radius: 10px;
            font-size: 0.85em;
            margin-top: 15px;
            text-align: center;
            color: #ffb3b3;
            animation: pulse 2s infinite;
        }}
        @keyframes pulse {{ 0% {{ opacity: 0.6; }} 50% {{ opacity: 1; }} 100% {{ opacity: 0.6; }} }}
        .progress-bg {{ background: rgba(255,255,255,0.1); height: 8px; border-radius: 4px; margin: 15px 0; overflow:hidden; }}
        .progress-fill {{ 
            background: linear-gradient(90deg, #415a77, #778da9, #e0e1dd); 
            width: {l['illum']}%; height: 100%; 
            box-shadow: 0 0 15px rgba(224, 225, 221, 0.5);
        }}
        .stat-row {{ display: flex; justify-content: space-between; font-size: 0.85em; opacity: 0.8; }}
    </style>

    <div class="moon-altar">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <div style="font-size: 3.5em; margin-bottom: -10px;">{l['phase_icon']}</div>
                <div class="moon-title">{l['tithi']} лунные сутки</div>
                <div style="color: #778da9; font-size: 0.95em;">
                    { "Растущая (Шукла)" if l['is_waxing'] else "Убывающая (Кришна)" } • {int(l['illum'])}% света
                </div>
            </div>
            <div style="text-align: right;">
                <div style="background: rgba(65, 90, 119, 0.3); padding: 10px 18px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.1);">
                    <div style="font-size: 1.2em; font-weight: bold; color: #e0e1dd;">{l['sign']}</div>
                    <div style="font-size: 0.85em; color: #778da9;">{l['nak']}</div>
                    <div style="font-size: 0.7em; color: #415a77; text-transform: uppercase; margin-top: 3px;">Лорд: {l['nak_lord']}</div>
                </div>
            </div>
        </div>
        <div class="progress-bg"><div class="progress-fill"></div></div>
        <div class="stat-row">
            <span>🌕 До Полнолуния: <b>{fmt_h(l['to_full'])}</b></span>
            <span>🌑 До Новолуния: <b>{fmt_h(l['to_new'])}</b></span>
        </div>
        {f'<div class="gandanta-alert">⚠️ ГАНДАНТА: {l["gandanta"]}</div>' if l['gandanta'] else ''}
        
     # Проверь, чтобы перед 💎 стояла открывающая кавычка функции markdown
    st.markdown(f"""
    <div style="margin-top: 20px; font-size: 0.9em; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px; color: #adb5bd;">
        💎 <b>Совет для AmK Луны:</b><br>
        {"Время транслировать идеи и расширять контакты." if l['is_waxing'] else "Время анализа и завершения текущих стратегий."}
    </div>
    """, unsafe_allow_html=True)

    # 3. ОСНОВНЫЕ МЕТРИКИ АК / AmK
    c1, c2 = st.columns(2)
    with c1:
        st.metric("💎 АК (Атма-карака)", get_full_info(df.iloc[0]))
    with c2:
        st.metric("🥈 AmK (Аматья-карака)", get_full_info(df.iloc[1]))

    # 4. ТАБЛИЦА ЧАРА-КАРАК
    st.subheader("📊 Таблица Чара-карак")
    df_v = df.copy()
    df_v['Знак'] = df_v['Lon'].apply(lambda x: Z_ICONS[ZODIAC_SIGNS[int(x/30)]])
    df_v['Накшатра'] = df_v['Lon'].apply(lambda x: f"{NAKSHATRAS[int(x/(360/27))%27]} ({NAK_LORDS[int(x/(360/27))%27]})")
    df_v['Градус'] = df_v['Deg'].apply(lambda x: f"{x:.4f}°")
    st.dataframe(df_v[['Role', 'Planet', 'Знак', 'Накшатра', 'Градус']], use_container_width=True, hide_index=True)

    st.divider()

    # 5. МОНИТОРИНГ РОТАЦИЙ (ИСПРАВЛЕННЫЙ ВЫЗОВ)
    st.subheader("🔄 Мониторинг ротаций")
    ak_now, amk_now = df.iloc[0]['Planet'], df.iloc[1]['Planet']
    
    cols = st.columns(2)
    settings = [(-1, "⬅️ Предыдущая смена", "#415A77"), (1, "➡️ Следующая смена", "#778DA9")]
    for idx, (direct, label_rot, color_rot) in enumerate(settings):
        with cols[idx]:
            st.markdown(f"<h4 style='color:{color_rot}; border-bottom:1px solid #eee;'>{label_rot}</h4>", unsafe_allow_html=True)
            for m in range(10, 2880, 10):
                target = now_utc + timedelta(minutes=m*direct)
                t_t = ts.utc(target.year, target.month, target.day, target.hour, target.minute)
                # ИСПРАВЛЕНИЕ: Принимаем только 2 значения (df_t и ayan)
                df_t, _ = get_planet_data(t_t) 
                if df_t.iloc[0]['Planet'] != ak_now or df_t.iloc[1]['Planet'] != amk_now:
                    st.success(f"📅 {(target + timedelta(hours=3)).strftime('%d.%m %H:%M')}")
                    st.caption(f"АК: {df_t.iloc[0]['Planet']} | AmK: {df_t.iloc[1]['Planet']}")
                    break
    
    # 6. МОДУЛЬ РАХУ
    ra_row = df[df['Planet'] == 'Rahu'].iloc[0]
    ra_deg = ra_row['Deg']
    
    if ra_deg < 2 or ra_deg > 28:
        label, color, desc = "🔴 КРИТИЧЕСКИЙ ХАОС", "#FF4B4B", "Зона Ганданты. Рынок иррационален."
    elif ra_deg < 5 or ra_deg > 25:
        label, color, desc = "🟡 ПОВЫШЕННЫЙ РИСК", "#FFA500", "Эмоциональные качели."
    else:
        label, color, desc = "🟢 ТЕХНИЧНЫЙ РЫНОК", "#00C853", "Чистая зона. Теханализ в норме."

    st.markdown(f"""<div style="background:{color}22; border-left:5px solid {color}; padding:15px; border-radius:10px; border:1px solid {color}44; margin-top:20px;">
        <h3 style="margin:0; color:{color};">🐲 Монитор Раху: {label}</h3>
        <p style="margin:5px 0;">{desc} (Градус: <b>{ra_deg:.2f}°</b>)</p></div>""", unsafe_allow_html=True)

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
        # Сочи UTC+3, для расчетов вычитаем 3 часа
        curr_utc = dt_start - timedelta(hours=3)
        end_utc = dt_end - timedelta(hours=3)
        events = []
        
        t_init = ts.utc(curr_utc.year, curr_utc.month, curr_utc.day, curr_utc.hour, curr_utc.minute)
        df_i, _ = get_planet_data(t_init)
        
        last_pair = f"{df_i.iloc[0]['Planet']}/{df_i.iloc[1]['Planet']}"
        events.append({
            "Время (Сочи)": dt_start.strftime("%d.%m.%Y %H:%M"), 
            "💎 АК": get_full_info(df_i.iloc[0]), 
            "🥈 AmK": get_full_info(df_i.iloc[1])
        })

        while curr_utc < end_utc:
            curr_utc += timedelta(minutes=5)
            t_s_loop = ts.utc(curr_utc.year, curr_utc.month, curr_utc.day, curr_utc.hour, curr_utc.minute)
            df_s, _ = get_planet_data(t_s_loop)
            
            new_pair = f"{df_s.iloc[0]['Planet']}/{df_s.iloc[1]['Planet']}"
            if new_pair != last_pair:
                sochi_time = curr_utc + timedelta(hours=3)
                events.append({
                    "Время (Сочи)": sochi_time.strftime("%d.%m.%Y %H:%M"), 
                    "💎 АК": get_full_info(df_s.iloc[0]), 
                    "🥈 AmK": get_full_info(df_s.iloc[1])
                })
                last_pair = new_pair
        
        if events:
            st.table(pd.DataFrame(events))
