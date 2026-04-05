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
# ✅ БЛОК 3: EDITABLE AREA (РАСЧЕТЫ И ЛОГИКА)
# ============================================================
def get_planet_data(t):
    current_ayan = get_dynamic_ayanamsa(t)
    earth = eph['earth']
    planets_objects = {'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 'Mercury': eph['mercury'], 'Jupiter': eph['jupiter_barycenter'], 'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']}
    res = []
    for name, obj in planets_objects.items():
        lon = (earth.at(t).observe(obj).ecliptic_latlon()[1].degrees - current_ayan) % 360
        res.append({'Planet': name, 'Lon': lon, 'Deg': lon % 30})
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    roles = ['AK', 'AmK', 'BK', 'MK', 'PiK', 'GK', 'DK']
    df['Role'] = roles[:len(df)]
    
    lat, lon, dist = earth.at(t).observe(eph['moon']).ecliptic_latlon()
    ra_lon = (lon.degrees - current_ayan + 180) % 360 
    ra_deg = 30 - (ra_lon % 30) 
    return df, current_ayan, ra_lon, ra_deg

def get_rahu_status(ra_deg):
    if ra_deg < 2 or ra_deg > 28:
        return "🔴 КРИТИЧЕСКИЙ ХАОС", "#FF4B4B", "Зона Ганданты/Сандхи. Максимальный риск манипуляций."
    elif ra_deg < 5 or ra_deg > 25:
        return "🟡 ПОВЫШЕННЫЙ РИСК", "#FFA500", "Рынок нестабилен. Эмоции доминируют над логикой."
    else:
        return "🟢 ТЕХНИЧНЫЙ РЫНОК", "#00C853", "Чистая зона. Теханализ и уровни работают штатно."

def get_rahu_forecast(start_t, days=30):
    """Сканирует будущее на предмет смены статуса Раху"""
    forecast = []
    last_status = None
    for d in range(days):
        check_t = start_t + timedelta(days=d)
        sky_t = ts.utc(check_t.year, check_t.month, check_t.day)
        _, _, _, r_deg = get_planet_data(sky_t)
        status, color, _ = get_rahu_status(r_deg)
        if status != last_status:
            forecast.append({"Дата": check_t.strftime("%d.%m.%Y"), "Статус": status, "color": color})
            last_status = status
    return forecast
    
# ============================================================
# ✅ БЛОК 4: EDITABLE AREA (ВКЛАДКИ И ОТОБРАЖЕНИЕ)
# ============================================================
tab1, tab2 = st.tabs(["📊 Прямой эфир", "📅 Высокоточный Таймлайн"])

with tab1:
    now_utc = datetime.utcnow()
    sochi_now = now_utc + timedelta(hours=3)
    t_now = ts.utc(now_utc.year, now_utc.month, now_utc.day, now_utc.hour, now_utc.minute, now_utc.second)
    
    # Получаем текущие данные
    df, ayan_val, rahu_lon, rahu_deg = get_planet_data(t_now)
    tithi, l_status, l_icon = get_lunar_info(t_now)
    
    st.markdown(f"**📍 Расчет на момент:** `{sochi_now.strftime('%d.%m.%Y %H:%M:%S')}` (Сочи)")

    # --- ВИДЖЕТ РАХУ ---
    ra_label, ra_color, ra_desc = get_rahu_status(rahu_deg)
    st.markdown(f"""
    <div style="background: {ra_color}22; border-left: 5px solid {ra_color}; padding: 15px; border-radius: 10px; margin-bottom: 10px; border: 1px solid {ra_color}44;">
        <h3 style="margin:0; color: {ra_color};">🐲 Монитор Раху: {ra_label}</h3>
        <p style="margin:5px 0; font-size: 1.1em; color: #1B263B;">{ra_desc}</p>
        <p style="margin:0; color: #d63384; font-weight: bold; font-size: 0.95em;">
            ⚠️ Внимание: когда линия на графике ниже приближается к 0° (граница знака), 
            в ближайшие дни золото может выдать любой финт, не поддающийся логике.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # --- ИСПРАВЛЕННЫЙ ГРАФИК (БЕЗ ГРЕБЕНКИ) ---
    st.subheader("📈 Тренд волатильности (Градус Раху в знаке)")
    
    # Создаем чистый список данных для графика
    chart_list = []
    # Идем строго по порядку от -15 дней до +45 дней
    for i in range(-15, 45):
        target_date = now_utc + timedelta(days=i)
        # Берем полдень для стабильности показаний
        t_check = ts.utc(target_date.year, target_date.month, target_date.day, 12, 0)
        _, _, _, r_deg = get_planet_data(t_check)
        
        chart_list.append({
            "Дата_сорт": target_date, # Для правильной сортировки
            "Дата": target_date.strftime("%d.%m"), 
            "Градус Раху": round(r_deg, 2)
        })
    
    # Превращаем в DataFrame и гарантируем порядок
    df_chart = pd.DataFrame(chart_list).sort_values("Дата_сорт")
    
    # Отрисовка
    st.line_chart(df_chart.set_index("Дата")["Градус Раху"], height=300)
    st.caption("Раху движется ретроградно. Плавное снижение к 0° означает приближение к зоне турбулентности.")

    # Календарь режимов
    with st.expander("📅 Календарь смены режимов рынка (60 дней)"):
        f_data = get_rahu_forecast(now_utc, 60)
        for item in f_data:
            st.markdown(f"**{item['Дата']}** — <span style='color:{item['color']}'>{item['Статус']}</span>", unsafe_allow_html=True)

    st.markdown("---")
    # Далее стандартная таблица АК/AmK и мониторинг...
