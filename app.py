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

# Вставь это в БЛОК 3. Добавлена функция поиска штормов для XAUUSD.
def get_xau_storms(t_start, days=45):
    storms = []
    earth = eph['earth']
    # Берем текущую айанамшу для точности
    ayan = get_dynamic_ayanamsa(t_start)
    
    for i in range(days):
        check_date = t_start + timedelta(days=i)
        t = ts.utc(check_date.year, check_date.month, check_date.day)
        
        # Позиция Солнца (Золото)
        sun_lon = (earth.at(t).observe(eph['sun']).ecliptic_latlon()[1].degrees - ayan) % 360
        # Позиция Раху
        _, _, ra_lon, ra_deg = get_planet_data(t)
        
        # Разность долгот
        diff = abs(sun_lon - ra_lon) % 360
        # Критические углы: 0 (соединение), 90 (квадрат), 180 (оппозиция)
        for p in [0, 90, 180, 270]:
            if abs(diff - p) < 3: # Орбис 3 градуса (зона влияния)
                storms.append({
                    "Дата": check_date.strftime("%d.%m"),
                    "Тип": "⚠️ ШТОРМ" if p in [0, 180] else "⚡️ ВОЛАТИЛЬНОСТЬ",
                    "Угол": f"{int(p)}°"
                })
                break
    # Убираем дубликаты дат
    seen = set()
    unique_storms = []
    for s in storms:
        if s["Дата"] not in seen:
            unique_storms.append(s)
            seen.add(s["Дата"])
    return unique_storms[:5] # Только ближайшие 5 событий
    
# ============================================================
# ✅ БЛОК 4: EDITABLE AREA (ВКЛАДКИ И ОТОБРАЖЕНИЕ)
# ============================================================
tab1, tab2 = st.tabs(["📊 Прямой эфир", "📅 Высокоточный Таймлайн"])

with tab1:
    now_utc = datetime.utcnow()
    sochi_now = now_utc + timedelta(hours=3)
    t_now = ts.utc(now_utc.year, now_utc.month, now_utc.day, now_utc.hour, now_utc.minute, now_utc.second)
    
    df, ayan_val, rahu_lon, rahu_deg = get_planet_data(t_now)
    tithi, l_status, l_icon = get_lunar_info(t_now)
    
    st.markdown(f"**📍 Расчет на момент:** `{sochi_now.strftime('%d.%m.%Y %H:%M:%S')}` (Сочи)")

    # --- НОВЫЙ РАДАР РАХУ ВМЕСТО ГРАФИКА ---
    ra_label, ra_color, ra_desc = get_rahu_status(rahu_deg)
    
    st.markdown(f"""
    <div style="background: {ra_color}22; border-left: 5px solid {ra_color}; padding: 15px; border-radius: 10px; margin-bottom: 20px; border: 1px solid {ra_color}44;">
        <h3 style="margin:0; color: {ra_color};">🐲 Монитор Раху: {ra_label}</h3>
        <p style="margin:5px 0;">{ra_desc} (Градус: {rahu_deg:.2f}°)</p>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("📡 Радар аномалий XAUUSD (Влияние на Золото)")
    col_r1, col_r2 = st.columns([1, 2])
    
    with col_r1:
        # Прогресс-бар "Давления" Раху
        # Если Раху у границ знака (0 или 30), давление растет
        risk_score = 100 - (rahu_deg * 5) if rahu_deg < 10 else (rahu_deg - 20) * 10 if rahu_deg > 20 else 5
        st.write("**Фоновое давление:**")
        st.progress(min(max(int(risk_score), 5), 100))
        st.caption("Близость к 'Ганданте' (0° или 30°)")

    with col_r2:
        st.write("**Ближайшие дни 'Мутного Рынка':**")
        storms = get_xau_storms(now_utc)
        if storms:
            for s in storms:
                st.warning(f"**{s['Дата']}** — {s['Тип']} (Аспект {s['Угол']})")
        else:
            st.success("✅ В ближайшие 30 дней Раху не блокирует Солнце. Рынок техничен.")

    st.info("💡 **Практическое применение:** В дни 'Шторма' Раху создает иллюзии. Золото может пробивать уровни на 100-200 пунктов и сразу возвращаться. Не торгуйте пробои, ждите подтверждения.")
    
    st.markdown("---")
    
    # Виджет Лунного цикла
    st.markdown(f"### {l_icon} Лунный цикл: {tithi} сутки ({l_status})")

    # Таблица Чара-карак
    df_v = df.copy()
    df_v['Знак'] = df_v['Lon'].apply(lambda x: Z_ICONS[ZODIAC_SIGNS[int(x/30)]])
    df_v['Накшатра'] = df_v['Lon'].apply(lambda x: f"{NAKSHATRAS[int(x/(360/27))%27]} ({NAK_LORDS[int(x/(360/27))%27]})")
    df_v['Градус'] = df_v['Deg'].apply(lambda x: f"{x:.4f}°")
    df_v.index = range(1, len(df_v) + 1)
    st.table(df_v[['Role', 'Planet', 'Знак', 'Накшатра', 'Градус']])

    # Мониторинг ротаций
    st.subheader("🔄 Мониторинг ротаций")
    c_cur1, c_cur2 = st.columns(2)
    with c_cur1: st.metric("💎 АК", get_full_info(df.iloc[0]))
    with c_cur2: st.metric("🥈 AmK", get_full_info(df.iloc[1]))

    ak_now, amk_now = df.iloc[0]['Planet'], df.iloc[1]['Planet']
    c1, c2 = st.columns(2)
    for col, direct, label, color in zip([c1, c2], [-1, 1], ["⬅️ Предыдущая", "➡️ Следующая"], ["#415A77", "#778DA9"]):
        with col:
            st.markdown(f"<h4 style='color:{color};'>{label}</h4>", unsafe_allow_html=True)
            for m in range(10, 2880, 10):
                target = now_utc + timedelta(minutes=m*direct)
                t_t = ts.utc(target.year, target.month, target.day, target.hour, target.minute)
                df_t, _, _, _ = get_planet_data(t_t)
                if df_t.iloc[0]['Planet'] != ak_now or df_t.iloc[1]['Planet'] != amk_now:
                    st.success(f"📅 {(target + timedelta(hours=3)).strftime('%d.%m %H:%M')}")
                    st.caption(f"АК: {get_full_info(df_t.iloc[0])} | AmK: {get_full_info(df_t.iloc[1])}")
                    break

with tab2:
    # (Весь код планировщика из прошлого сообщения остается без изменений, 
    #  просто убедись, что вызов функции там df_i, _, _, _ = get_planet_data(t_init))
    st.header("📅 Высокоточный планировщик")
    dt_s = datetime.combine(st.date_input("С", key="sd_tl"), st.time_input("С время", key="st_tl"))
    dt_e = datetime.combine(st.date_input("ПО", key="ed_tl"), st.time_input("ПО время", key="et_tl"))
    if st.button('🚀 Рассчитать бланк'):
        with st.spinner('Синхронизация...'):
            curr_u, end_u, events = dt_s - timedelta(hours=3), dt_e - timedelta(hours=3), []
            t_init = ts.utc(curr_u.year, curr_u.month, curr_u.day, curr_u.hour, curr_u.minute)
            df_i, _, _, _ = get_planet_data(t_init)
            last_p = f"{df_i.iloc[0]['Planet']}/{df_i.iloc[1]['Planet']}"
            events.append({"Время (Сочи)": dt_s.strftime("%d.%m %H:%M"), "АК": get_full_info(df_i.iloc[0]), "AmK": get_full_info(df_i.iloc[1])})
            tmp = curr_u
            while tmp < end_u:
                tmp += timedelta(minutes=1)
                ts_step = ts.utc(tmp.year, tmp.month, tmp.day, tmp.hour, tmp.minute)
                df_s, _, _, _ = get_planet_data(ts_step)
                new_p = f"{df_s.iloc[0]['Planet']}/{df_s.iloc[1]['Planet']}"
                if new_p != last_p:
                    events.append({"Время (Сочи)": (tmp + timedelta(hours=3)).strftime("%d.%m %H:%M"), "АК": get_full_info(df_s.iloc[0]), "AmK": get_full_info(df_s.iloc[1])})
                    last_p = new_p
            st.table(pd.DataFrame(events))
