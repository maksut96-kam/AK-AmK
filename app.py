# ============================================================
# ⛔ БЛОК 1: DO NOT TOUCH (ФУНДАМЕНТ И ИМПОРТЫ)
# ============================================================
import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd
import streamlit.components.v1 as components
import math
import os
import base64

st.set_page_config(page_title="Julia Assistant Astro Coordination Center", layout="wide")

@st.cache_resource
def init_engine():
    ts = load.timescale()
    eph = load('de421.bsp')
    return ts, eph

ts, eph = init_engine()

ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]
NAK_LORDS = ["Кету", "Венера", "Солнце", "Луна", "Марс", "Раху", "Юпитер", "Сатурн", "Меркурий"] * 3
P_ICONS = {'Sun': '☀️ Sun', 'Moon': '🌙 Moon', 'Mars': '🔴 Mars', 'Mercury': '☿️ Merc', 'Jupiter': '🔵 Jup', 'Venus': '♀️ Venus', 'Saturn': '🪐 Sat'}
Z_ICONS = {"Овен": "♈ Овен", "Телец": "♉ Телец", "Близнецы": "♊ Близн", "Рак": "♋ Рак", "Лев": "♌ Лев", "Дева": "♍ Дева", "Весы": "♎ Весы", "Скорпион": "♏ Скорп", "Стрелец": "♐ Стрел", "Козерог": "♑ Козег", "Водолей": "♒ Водол", "Рыбы": "♓ Рыбы"}

def get_dynamic_ayanamsa(t):
    T = (t.tt - 2451545.0) / 36525.0
    return 23.856235 + (2.30142 * T) + (0.000139 * T**2)

def format_deg_to_min(deg_float):
    d = int(deg_float); m = int((deg_float - d) * 60); s = round((((deg_float - d) * 60) - m) * 60, 2)
    return f"{d}° {m}' {s}\""

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

# ============================================================
# ⛔ БЛОК 2: DO NOT TOUCH (ШАПКА И ЛОГОТИП)
# ============================================================
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

# ============================================================
# 🧮 БЛОК 3: МАТЕМАТИЧЕСКОЕ ЯДРО (РАСЧЕТЫ И АСТРО-ЛОГИКА)
# ============================================================

# --- Подблок 3.1: Базовые вычисления ---
def get_dynamic_ayanamsa(t_skyfield):
    """Вычисляет айанамшу Лахири на текущий момент времени."""
    jd = t_skyfield.tt
    t_centuries = (jd - 2451545.0) / 36525
    return 23.85 + (50.3 / 3600) * t_centuries

def get_planet_data(t):
    """Рассчитывает координаты 7 планет, их роли (АК/AmK) и положение Раху."""
    current_ayan = get_dynamic_ayanamsa(t)
    earth = eph['earth']
    planets_objects = {
        'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 
        'Mercury': eph['mercury'], 'Jupiter': eph['jupiter_barycenter'], 
        'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']
    }
    res = []
    for name, obj in planets_objects.items():
        lon = (earth.at(t).observe(obj).ecliptic_latlon()[1].degrees - current_ayan) % 360
        res.append({'Planet': name, 'Lon': lon, 'Deg': lon % 30})
    
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    df['Role'] = ['AK', 'AmK', 'BK', 'MK', 'PiK', 'GK', 'DK'][:len(df)]
    
    # Раху (всегда ретрограден в нашей логике: от 30 к 0)
    lat, lon, dist = earth.at(t).observe(eph['moon']).ecliptic_latlon()
    ra_lon = (lon.degrees - current_ayan + 180) % 360 
    ra_deg = 30 - (ra_lon % 30) 
    return df, ra_lon, ra_deg

# --- Подблок 3.2: Логика Луны и Раху ---
def get_lunar_data(t):
    """Определяет титхи (лунные сутки), статус и иконку фазы."""
    sun_lon = eph['earth'].at(t).observe(eph['sun']).ecliptic_latlon()[1].degrees
    moon_lon = eph['earth'].at(t).observe(eph['moon']).ecliptic_latlon()[1].degrees
    diff = (moon_lon - sun_lon) % 360
    tithi = int(diff / 12) + 1
    status = "Растущая (Шукла)" if diff < 180 else "Убывающая (Кришна)"
    icon = "🌙" if diff < 180 else "🌘"
    return tithi, status, icon

def get_xau_storms(dt_start, days=45):
    """Ищет критические аспекты Раху к Солнцу (Золоту) на 45 дней вперед."""
    storms = []
    earth = eph['earth']
    for i in range(days):
        check_date = dt_start + timedelta(days=i)
        t_check = ts.utc(check_date.year, check_date.month, check_date.day)
        ayan = get_dynamic_ayanamsa(t_check)
        sun_lon = (earth.at(t_check).observe(eph['sun']).ecliptic_latlon()[1].degrees - ayan) % 360
        _, _, ra_lon_c = get_planet_data(t_check) # ra_lon_c здесь не используется напрямую, берем из функции
        
        # Получаем данные Раху для этой даты
        _, ra_lon_check, _ = get_planet_data(t_check)
        diff = abs(sun_lon - ra_lon_check) % 360
        
        # Соединение (0), Квадрат (90), Оппозиция (180)
        for p in [0, 90, 180, 270]:
            if abs(diff - p) < 3:
                storms.append({
                    "Дата": check_date.strftime("%d.%m"), 
                    "Тип": "⚠️ ШТОРМ" if p in [0, 180] else "⚡️ ВОЛАТИЛЬНОСТЬ", 
                    "Угол": f"{int(p)}°"
                })
                break
    # Фильтр уникальных дат
    seen, unique = set(), []
    for s in storms:
        if s["Дата"] not in seen: unique.append(s); seen.add(s["Дата"])
    return unique[:5]

# --- Подблок 3.3: Форматирование вывода ---
def get_full_info(row):
    """Превращает строку данных планеты в читаемый текст с иконкой знака."""
    sign = ZODIAC_SIGNS[int(row['Lon']/30)]
    return f"{row['Planet']} ({Z_ICONS[sign]} {sign} {row['Deg']:.2f}°)"

# ============================================================
# 🔵 МОДУЛЬ 4.1: ВИДЖЕТ РАХУ (РАДАР ШТОРМОВ XAUUSD)
# ============================================================
def render_rahu_module(ra_deg, now_dt):
    if ra_deg < 2 or ra_deg > 28: label, color, desc = "🔴 КРИТИЧЕСКИЙ ХАОС", "#FF4B4B", "Зона Ганданты. Рынок крайне иррационален."
    elif ra_deg < 5 or ra_deg > 25: label, color, desc = "🟡 ПОВЫШЕННЫЙ РИСК", "#FFA500", "Эмоциональные качели. Возможны сквизы."
    else: label, color, desc = "🟢 ТЕХНИЧНЫЙ РЫНОК", "#00C853", "Чистая зона. Теханализ в норме."

    st.markdown(f"""<div style="background:{color}22; border-left:5px solid {color}; padding:15px; border-radius:10px; border:1px solid {color}44;">
        <h3 style="margin:0; color:{color};">🐲 Монитор Раху: {label}</h3>
        <p style="margin:5px 0;">{desc} (Текущий градус: <b>{ra_deg:.2f}°</b>)</p></div>""", unsafe_allow_html=True)

    st.subheader("📡 Радар аномалий XAUUSD")
    c1, c2 = st.columns([1, 2])
    with c1:
        score = 100-(ra_deg*5) if ra_deg<10 else (ra_deg-20)*10 if ra_deg>20 else 5
        st.write("**Давление Раху:**"); st.progress(min(max(int(score), 5), 100))
    with c2:
        storms = get_xau_storms(now_dt)
        if storms:
            for s in storms: st.warning(f"**{s['Дата']}** — {s['Тип']} (Угол {s['Угол']})")
        else: st.success("✅ Критических помех для золота не обнаружено.")

# ============================================================
# 🌙 МОДУЛЬ 4.2: ВИДЖЕТ ЛУНЫ
# ============================================================
def render_lunar_module(tithi, status, icon):
    st.markdown(f"### {icon} Лунный цикл: {tithi} сутки")
    st.info(f"Текущая фаза: **{status}**")

# ============================================================
# 💎 МОДУЛЬ 4.3: ТЕКУЩИЕ АК И АмК (ТАБЛИЦА)
# ============================================================
def render_karakas_table(df):
    st.subheader("📊 Таблица Чара-карак")
    df_v = df.copy()
    df_v['Знак'] = df_v['Lon'].apply(lambda x: Z_ICONS[ZODIAC_SIGNS[int(x/30)]])
    df_v['Накшатра'] = df_v['Lon'].apply(lambda x: f"{NAKSHATRAS[int(x/(360/27))%27]} ({NAK_LORDS[int(x/(360/27))%27]})")
    df_v['Градус'] = df_v['Deg'].apply(lambda x: f"{x:.4f}°")
    df_v.index = range(1, len(df_v) + 1)
    st.table(df_v[['Role', 'Planet', 'Знак', 'Накшатра', 'Градус']])

# ============================================================
# 🔄 МОДУЛЬ 4.4: МОНИТОРИНГ РОТАЦИЙ (БЛИЖАЙШИЕ СМЕНЫ)
# ============================================================
def render_rotation_monitor(df, now_utc):
    st.subheader("🔄 Мониторинг ротаций")
    ak_now, amk_now = df.iloc[0]['Planet'], df.iloc[1]['Planet']
    
    c_m1, c_m2 = st.columns(2)
    with c_m1: st.metric("💎 Текущая АК", get_full_info(df.iloc[0]))
    with c_m2: st.metric("🥈 Текущая AmK", get_full_info(df.iloc[1]))

    cols = st.columns(2)
    settings = [(-1, "⬅️ Предыдущая смена", "#415A77"), (1, "➡️ Следующая смена", "#778DA9")]
    for idx, (direct, label, color) in enumerate(settings):
        with cols[idx]:
            st.markdown(f"<h4 style='color:{color}; border-bottom:1px solid #eee;'>{label}</h4>", unsafe_allow_html=True)
            for m in range(10, 2880, 10):
                target = now_utc + timedelta(minutes=m*direct)
                t_t = ts.utc(target.year, target.month, target.day, target.hour, target.minute)
                df_t, _, _ = get_planet_data(t_t)
                if df_t.iloc[0]['Planet'] != ak_now or df_t.iloc[1]['Planet'] != amk_now:
                    st.success(f"📅 {(target + timedelta(hours=3)).strftime('%d.%m %H:%M')}")
                    st.caption(f"АК: {get_full_info(df_t.iloc[0])}\n\nAmK: {get_full_info(df_t.iloc[1])}")
                    break

# ============================================================
# 🚀 ГЛАВНЫЙ СБОРОЧНЫЙ ЦЕХ (TABS)
# ============================================================

tab1, tab2 = st.tabs(["📊 Прямой эфир", "📅 Высокоточный Планировщик"])

# --- ВКЛАДКА 1: ОПЕРАТИВНЫЙ МОНИТОРИНГ ---
with tab1:
    now_utc = datetime.utcnow()
    t_now = ts.utc(now_utc.year, now_utc.month, now_utc.day, now_utc.hour, now_utc.minute, now_utc.second)
    df, ra_lon, ra_deg = get_planet_data(t_now)
    tithi, l_status, l_icon = get_lunar_data(t_now)
    
    st.markdown(f"**📍 Расчет (Сочи):** `{(now_utc + timedelta(hours=3)).strftime('%d.%m.%Y %H:%M:%S')}`")

    render_rahu_module(ra_deg, now_utc)
    st.markdown("---")
    render_lunar_module(tithi, l_status, l_icon)
    st.markdown("---")
    render_karakas_table(df)
    st.markdown("---")
    render_rotation_monitor(df, now_utc)

# --- ВКЛАДКА 2: ИНСТРУМЕНТ ПРОГНОЗИРОВАНИЯ ---
with tab2:
    st.header("📅 Высокоточный планировщик ротаций")
    st.write("Инструмент для поиска точного времени смены АК и AmK на выбранном периоде.")
    
    c_p1, c_p2 = st.columns(2)
    with c_p1:
        d_s = st.date_input("Дата начала", value=datetime.now(), key="ds_p")
        t_s = st.time_input("Время начала", value=time(0, 0), key="ts_p")
    with c_p2:
        d_e = st.date_input("Дата конца", value=datetime.now() + timedelta(days=3), key="de_p")
        t_e = st.time_input("Время конца", value=time(23, 59), key="te_p")

    if st.button('🚀 Рассчитать и подготовить бланк'):
        dt_start = datetime.combine(d_s, t_s)
        dt_end = datetime.combine(d_e, t_e)
        
        if dt_start >= dt_end:
            st.error("Ошибка: Время начала должно быть раньше времени завершения.")
        else:
            with st.spinner('Синхронизация планетарных циклов...'):
                curr_utc = dt_start - timedelta(hours=3)
                end_utc = dt_end - timedelta(hours=3)
                events = []
                
                # Начальное состояние
                t_init = ts.utc(curr_utc.year, curr_utc.month, curr_utc.day, curr_utc.hour, curr_utc.minute)
                df_i, _, _ = get_planet_data(t_init)
                last_pair = f"{df_i.iloc[0]['Planet']}/{df_i.iloc[1]['Planet']}"
                
                # Добавляем стартовую точку
                events.append({
                    "Время (Сочи)": dt_start.strftime("%d.%m.%Y %H:%M"),
                    "💎 АК": get_full_info(df_i.iloc[0]),
                    "🥈 AmK": get_full_info(df_i.iloc[1])
                })
                
                # Цикл поиска изменений
                temp_time = curr_utc
                while temp_time < end_utc:
                    temp_time += timedelta(minutes=1)
                    t_step = ts.utc(temp_time.year, temp_time.month, temp_time.day, temp_time.hour, temp_time.minute)
                    df_step, _, _ = get_planet_data(t_step)
                    new_pair = f"{df_step.iloc[0]['Planet']}/{df_step.iloc[1]['Planet']}"
                    
                    if new_pair != last_pair:
                        events.append({
                            "Время (Сочи)": (temp_time + timedelta(hours=3)).strftime("%d.%m.%Y %H:%M"),
                            "💎 АК": get_full_info(df_step.iloc[0]),
                            "🥈 AmK": get_full_info(df_step.iloc[1])
                        })
                        last_pair = new_pair
                
                st.success(f"Найдено ротаций: {len(events)-1}")
                st.table(pd.DataFrame(events))
