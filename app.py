# ============================================================
# ⛔ БЛОК 1: ФУНДАМЕНТ, ИМПОРТЫ И КОНСТАНТЫ
# ============================================================
import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta, time
import pandas as pd
import math
import base64

# Настройка страницы должна быть ПЕРВОЙ командой
st.set_page_config(page_title="Julia Assistant Astro Coordination Center", layout="wide")

@st.cache_resource
def init_engine():
    ts = load.timescale()
    try:
        eph = load('de421.bsp')
    except:
        eph = load('https://jplv.github.io/jplv/de421.bsp') # Резервный канал загрузки
    return ts, eph

ts, eph = init_engine()

# --- СЛОВАРИ И ИКОНКИ ---
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]
NAK_LORDS = ["Кету", "Венера", "Солнце", "Луна", "Марс", "Раху", "Юпитер", "Сатурн", "Меркурий"] * 3
P_ICONS = {'Sun': '☀️ Sun', 'Moon': '🌙 Moon', 'Mars': '🔴 Mars', 'Mercury': '☿️ Merc', 'Jupiter': '🔵 Jup', 'Venus': '♀️ Venus', 'Saturn': '🪐 Sat'}
Z_ICONS = {"Овен": "♈ Овен", "Телец": "♉ Телец", "Близнецы": "♊ Близн", "Рак": "♋ Рак", "Лев": "♌ Лев", "Дева": "♍ Дева", "Весы": "♎ Весы", "Скорпион": "♏ Скорп", "Стрелец": "♐ Стрел", "Козерог": "♑ Козег", "Водолей": "♒ Водол", "Рыбы": "♓ Рыбы"}

# ============================================================
# 🧮 БЛОК 2: МАТЕМАТИЧЕСКИЕ ВЫЧИСЛЕНИЯ
# ============================================================

def get_dynamic_ayanamsa(t):
    T = (t.tt - 2451545.0) / 36525.0
    return 23.856235 + (2.30142 * T) + (0.000139 * T**2)

def get_full_info(row):
    nak_idx = int(row['Lon'] / (360/27)) % 27
    sign = ZODIAC_SIGNS[int(row['Lon'] / 30)]
    return f"{P_ICONS.get(row['Planet'], row['Planet'])} | {Z_ICONS.get(sign, sign)} | ☸️ {NAKSHATRAS[nak_idx]} ({NAK_LORDS[nak_idx]})"

def get_planet_data(t):
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
    
    # Расчет Раху (Средний узел)
    m_lon = earth.at(t).observe(eph['moon']).ecliptic_latlon()[1].degrees
    ra_lon = (m_lon - current_ayan + 180) % 360 
    ra_deg = 30 - (ra_lon % 30) 
    return df, ra_lon, ra_deg

def get_lunar_info(t):
    earth = eph['earth']
    s_lon = earth.at(t).observe(eph['sun']).ecliptic_latlon()[1].degrees
    m_lon = earth.at(t).observe(eph['moon']).ecliptic_latlon()[1].degrees
    diff = (m_lon - s_lon) % 360
    tithi = math.ceil(diff / 12) or 1
    icon = ["🌑","🌒","🌓","🌔","🌕","🌖","🌗","🌘"][int(diff/45) % 8]
    status = "Растущая (Шукла)" if diff < 180 else "Убывающая (Кришна)"
    return tithi, status, icon

def get_xau_storms(dt_now):
    # Упрощенный поиск штормов (аспекты Раху к Солнцу)
    storms = []
    for i in range(30):
        d = dt_now + timedelta(days=i)
        t_c = ts.utc(d.year, d.month, d.day)
        ayan = get_dynamic_ayanamsa(t_c)
        s_lon = (eph['earth'].at(t_c).observe(eph['sun']).ecliptic_latlon()[1].degrees - ayan) % 360
        _, r_lon, _ = get_planet_data(t_c)
        if abs(s_lon - r_lon) % 90 < 2:
            storms.append({"Дата": d.strftime("%d.%m"), "Тип": "⚠️ ШТОРМ", "Угол": "90/180°"})
            if len(storms) >= 3: break
    return storms

def create_printable_html(df, title_period):
    rows_html = ""
    for _, row in df.iterrows():
        rows_html += f"<tr><td style='border:1px solid #ddd;padding:12px;'>{row['Время (Сочи)']}</td><td style='border:1px solid #ddd;padding:12px;'><b>АК:</b> {row['💎 АК']}<br><b>AmK:</b> {row['🥈 AmK']}</td></tr>"
    return f"<html><body style='font-family:sans-serif;'><h2>План ротаций: {title_period}</h2><table style='width:100%;border-collapse:collapse;'>{rows_html}</table></body></html>"

# ============================================================
# 🖥️ БЛОК 3: МОДУЛИ ОТОБРАЖЕНИЯ (UI)
# ============================================================

def render_rahu_module(ra_deg, now_dt):
    if ra_deg < 2 or ra_deg > 28: label, color, desc = "🔴 КРИТИЧЕСКИЙ ХАОС", "#FF4B4B", "Зона Ганданты. Рынок крайне иррационален."
    elif ra_deg < 5 or ra_deg > 25: label, color, desc = "🟡 ПОВЫШЕННЫЙ РИСК", "#FFA500", "Эмоциональные качели. Возможны сквизы."
    else: label, color, desc = "🟢 ТЕХНИЧНЫЙ РЫНОК", "#00C853", "Чистая зона. Теханализ в норме."

    st.markdown(f"""<div style="background:{color}22; border-left:5px solid {color}; padding:15px; border-radius:10px; border:1px solid {color}44;">
        <h3 style="margin:0; color:{color};">🐲 Монитор Раху: {label}</h3>
        <p style="margin:5px 0;">{desc} (Текущий градус: <b>{ra_deg:.2f}°</b>)</p></div>""", unsafe_allow_html=True)

    st.subheader("📡 Радар аномалий XAUUSD")
    storms = get_xau_storms(now_dt)
    if storms:
        cols = st.columns(len(storms))
        for i, s in enumerate(storms):
            cols[i].warning(f"**{s['Дата']}**\n\n{s['Тип']}")
    else:
        st.success("✅ Критических помех для золота не обнаружено.")

def render_lunar_module(tithi, status, icon):
    st.markdown(f"### {icon} Лунный цикл: {tithi} сутки")
    st.info(f"Текущая фаза: **{status}**")

def render_karakas_table(df):
    st.subheader("📊 Таблица Чара-карак")
    df_v = df.copy()
    df_v['Знак'] = df_v['Lon'].apply(lambda x: Z_ICONS.get(ZODIAC_SIGNS[int(x/30)], "??"))
    df_v['Накшатра'] = df_v['Lon'].apply(lambda x: f"{NAKSHATRAS[int(x/(360/27))%27]} ({NAK_LORDS[int(x/(360/27))%27]})")
    df_v['Градус'] = df_v['Deg'].apply(lambda x: f"{x:.4f}°")
    st.table(df_v[['Role', 'Planet', 'Знак', 'Накшатра', 'Градус']])

def render_rotation_monitor(df, now_utc):
    st.subheader("🔄 Мониторинг ротаций")
    ak_now, amk_now = df.iloc[0]['Planet'], df.iloc[1]['Planet']
    c1, c2 = st.columns(2)
    c1.metric("💎 Текущая АК", get_full_info(df.iloc[0]))
    c2.metric("🥈 Текущая AmK", get_full_info(df.iloc[1]))
    
    # Поиск ближайшей смены
    st.markdown("#### Ближайшие изменения:")
    col_past, col_future = st.columns(2)
    
    for direction, label, col_obj in [(-1, "⬅️ Было", col_past), (1, "➡️ Будет", col_future)]:
        with col_obj:
            for m in range(10, 2880, 10):
                target = now_utc + timedelta(minutes=m*direction)
                t_t = ts.utc(target.year, target.month, target.day, target.hour, target.minute)
                df_t, _, _ = get_planet_data(t_t)
                if df_t.iloc[0]['Planet'] != ak_now or df_t.iloc[1]['Planet'] != amk_now:
                    st.write(f"**{label}:**")
                    st.success(f"{(target + timedelta(hours=3)).strftime('%d.%m %H:%M')}")
                    break

# ============================================================
# 🚀 БЛОК 4: ГЛАВНЫЙ СБОРОЧНЫЙ ЦЕХ (APP LOOP)
# ============================================================

try:
    tab1, tab2 = st.tabs(["📊 Прямой эфир", "📅 Высокоточный Планировщик"])

    with tab1:
        # 1. Сбор данных
        now_utc = datetime.utcnow()
        t_now = ts.utc(now_utc.year, now_utc.month, now_utc.day, now_utc.hour, now_utc.minute, now_utc.second)
        
        df_current, ra_lon_current, ra_deg_current = get_planet_data(t_now)
        tithi, l_status, l_icon = get_lunar_info(t_now)

        # 2. Отрисовка блоков
        render_rahu_module(ra_deg_current, now_utc)
        st.markdown("---")
        render_lunar_module(tithi, l_status, l_icon)
        st.markdown("---")
        render_karakas_table(df_current)
        st.markdown("---")
        render_rotation_monitor(df_current, now_utc)

    with tab2:
        st.header("📅 Высокоточный планировщик")
        col_in1, col_in2 = st.columns(2)
        d_s = col_in1.date_input("Начало", datetime.now())
        t_s = col_in1.time_input("Время начала", time(0, 0))
        d_e = col_in2.date_input("Конец", datetime.now() + timedelta(days=2))
        t_e = col_in2.time_input("Время конца", time(23, 59))
        
        if st.button("🚀 Найти ротации"):
            dt_start = datetime.combine(d_s, t_s)
            dt_end = datetime.combine(d_e, t_e)
            
            with st.spinner("Сканирование эфира..."):
                curr = dt_start - timedelta(hours=3)
                stop = dt_end - timedelta(hours=3)
                results = []
                
                # Исходная точка
                t_init = ts.utc(curr.year, curr.month, curr.day, curr.hour, curr.minute)
                df_i, _, _ = get_planet_data(t_init)
                last_p = f"{df_i.iloc[0]['Planet']}{df_i.iloc[1]['Planet']}"
                results.append({"Время (Сочи)": dt_start.strftime("%d.%m %H:%M"), "💎 АК": get_full_info(df_i.iloc[0]), "🥈 AmK": get_full_info(df_i.iloc[1])})
                
                while curr < stop:
                    curr += timedelta(minutes=5) # Шаг 5 мин для скорости
                    t_step = ts.utc(curr.year, curr.month, curr.day, curr.hour, curr.minute)
                    df_s, _, _ = get_planet_data(t_step)
                    new_p = f"{df_s.iloc[0]['Planet']}{df_s.iloc[1]['Planet']}"
                    if new_p != last_p:
                        results.append({"Время (Сочи)": (curr + timedelta(hours=3)).strftime("%d.%m %H:%M"), "💎 АК": get_full_info(df_s.iloc[0]), "🥈 AmK": get_full_info(df_s.iloc[1])})
                        last_p = new_p
                
                st.table(pd.DataFrame(results))
                
                # Экспорт
                html = create_printable_html(pd.DataFrame(results), f"{d_s} - {d_e}")
                b64 = base64.b64encode(html.encode()).decode()
                st.markdown(f'<a href="data:text/html;base64,{b64}" download="plan.html"><button style="width:100%; border-radius:5px; height:40px; background:#1B263B; color:white; border:none;">📥 Скачать для печати</button></a>', unsafe_allow_html=True)

except Exception as e:
    st.error(f"Произошла ошибка при запуске: {e}")
    st.info("Попробуйте перезагрузить страницу. Если ошибка повторяется, проверьте наличие файла de421.bsp.")
