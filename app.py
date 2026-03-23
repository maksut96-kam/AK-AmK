import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd
import streamlit.components.v1 as components
import math

# 1. Системные настройки
st.set_page_config(page_title="Julia Assistant Astro", layout="wide")

@st.cache_resource
def init_engine():
    ts = load.timescale()
    # Используем de421 для высокой точности
    eph = load('de421.bsp')
    return ts, eph

ts, eph = init_engine()

# --- Константы и Словари ---
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]

P_ICONS = {
    'Sun': '☀️ Sun', 'Moon': '🌙 Moon', 'Mars': '🔴 Mars', 
    'Mercury': '☿️ Merc', 'Jupiter': '🔵 Jup', 'Venus': '♀️ Venus', 
    'Saturn': '🪐 Sat', 'Rahu': '🐲 Rahu', 'Ketu': '🐍 Ketu'
}
Z_ICONS = {
    "Овен": "♈ Овен", "Телец": "♉ Телец", "Близнецы": "♊ Близн", "Рак": "♋ Рак", 
    "Лев": "♌ Лев", "Дева": "♍ Дева", "Весы": "♎ Весы", "Скорпион": "♏ Скорп", 
    "Стрелец": "♐ Стрел", "Козерог": "♑ Козег", "Водолей": "♒ Водол", "Рыбы": "♓ Рыбы"
}

def get_dynamic_ayanamsa(t):
    T = (t.tt - 2451545.0) / 36525.0
    ayan = 23.856235 + (2.30142 * T) + (0.000139 * T**2)
    return ayan

def format_deg_to_min(deg_float):
    d = int(deg_float)
    m = int((deg_float - d) * 60)
    s = round((((deg_float - d) * 60) - m) * 60, 1)
    return f"{d}° {m}' {s}\""

def get_planet_data(t):
    current_ayan = get_dynamic_ayanamsa(t)
    earth = eph['earth']
    
    planets_objects = {
        'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 
        'Mercury': eph['mercury'], 'Jupiter': eph['jupiter_barycenter'], 
        'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']
    }
    
    res = []
    # Основные 7 планет
    for name, obj in planets_objects.items():
        lon = (earth.at(t).observe(obj).ecliptic_latlon()[1].degrees - current_ayan) % 360
        res.append({'Planet': name, 'Lon': lon, 'Deg': lon % 30})
    
    # Раху (Mean Rahu - расчет через положение Луны)
    lat, lon, distance = earth.at(t).observe(eph['moon']).ecliptic_latlon()
    ra_lon = (lon.degrees - current_ayan + 180) % 360 
    # В Джйотише для Чара-карак градус Раху часто инвертируют (30 - градус), так как он идет назад
    res.append({'Planet': 'Rahu', 'Lon': ra_lon, 'Deg': 30 - (ra_lon % 30)}) 
    
    # Сортировка для Чара-карак (AK, AmK и т.д.)
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    roles = ['AK', 'AmK', 'BK', 'MK', 'PiK', 'PK', 'GK', 'DK']
    df['Role'] = roles[:len(df)]
    
    # Кету (справочно)
    ketu_lon = (ra_lon + 180) % 360
    ketu_row = pd.DataFrame([{'Planet': 'Ketu', 'Lon': ketu_lon, 'Deg': ketu_lon % 30, 'Role': '-'}])
    df = pd.concat([df, ketu_row], ignore_index=True)
    
    return df, current_ayan

def get_lunar_info(t, eph):
    earth = eph['earth']
    s_lon = earth.at(t).observe(eph['sun']).ecliptic_latlon()[1].degrees
    m_lon = earth.at(t).observe(eph['moon']).ecliptic_latlon()[1].degrees
    
    diff = (m_lon - s_lon) % 360
    tithi_num = math.ceil(diff / 12)
    if tithi_num <= 0: tithi_num = 1
    
    if 0 <= diff < 45: phase_icon = "🌑"
    elif 45 <= diff < 90: phase_icon = "🌒"
    elif 90 <= diff < 135: phase_icon = "🌓"
    elif 135 <= diff < 180: phase_icon = "🌔"
    elif 180 <= diff < 225: phase_icon = "🌕"
    elif 225 <= diff < 270: phase_icon = "🌖"
    elif 270 <= diff < 315: phase_icon = "🌗"
    else: phase_icon = "🌘"
    
    status = "Растущая (Шукла Пакша)" if diff < 180 else "Убывающая (Кришна Пакша)"
    return tithi_num, status, phase_icon

def get_full_info(row):
    nak_idx = int(row['Lon'] / (360/27)) % 27
    nak = NAKSHATRAS[nak_idx]
    sign = ZODIAC_SIGNS[int(row['Lon'] / 30)]
    p_name = row['Planet']
    return f"{P_ICONS.get(p_name, p_name)} | {Z_ICONS.get(sign, sign)} | ☸️ {nak}"

# --- ИНТЕРФЕЙС ---
st.markdown("<h1 style='text-align: center; color: #6A5ACD;'>✨ Julia Assistant Astro Coordination Center ✨</h1>", unsafe_allow_html=True)

# Часы Сочи через HTML/JS
components.html("""
    <div style="background: linear-gradient(90deg, #e0eafc, #cfdef3); padding:15px; border-radius:15px; text-align:center; font-family: 'Segoe UI', sans-serif; box-shadow: 2px 2px 10px rgba(0,0,0,0.1);">
        <h2 id="clock" style="margin:0; color:#4B0082;">Загрузка...</h2>
        <p style="margin:0; color:#555; font-weight: bold;">Sochi Time (UTC+3)</p>
    </div>
    <script>
        function updateClock() {
            let d = new Date();
            let utc = d.getTime() + (d.getTimezoneOffset() * 60000);
            let sochi = new Date(utc + (3600000 * 3));
            document.getElementById('clock').innerHTML = sochi.toLocaleTimeString('ru-RU');
        }
        setInterval(updateClock, 1000);
        updateClock();
    </script>
""", height=120)

tab1, tab2 = st.tabs(["🌟 Прямой эфир", "📅 План на неделю"])

with tab1:
    now = datetime.utcnow()
    t_now = ts.utc(now.year, now.month, now.day, now.hour, now.minute, now.second)
    df, ayan_val = get_planet_data(t_now)
    tithi, l_status, l_icon = get_lunar_info(t_now, eph)

    st.markdown(f"""
    <div style="background: #fffafa; border-left: 5px solid #6A5ACD; padding: 20px; border-radius: 10px; margin-bottom: 20px;">
        <h3 style="margin-top:0;">{l_icon} Статус Луны</h3>
        <p style="font-size: 1.2em; margin-bottom:5px;"><b>Лунные сутки (Титхи):</b> {tithi}</p>
        <p style="font-size: 1.1em; color: #444; margin-top:0;">{l_status}</p>
    </div>
    """, unsafe_allow_html=True)

    st.info(f"🔮 **Айанамша Лахири (динамическая):** {format_deg_to_min(ayan_val)}")
    
    df_v = df.copy()
    df_v['Знак'] = df_v['Lon'].apply(lambda x: Z_ICONS.get(ZODIAC_SIGNS[int(x/30)], ZODIAC_SIGNS[int(x/30)]))
    df_v['Накшатра'] = df_v['Lon'].apply(lambda x: NAKSHATRAS[int(x / (360/27)) % 27])
    df_v['Градус'] = df_v['Deg'].apply(lambda x: f"{x:.4f}°")
    
    st.table(df_v[['Role', 'Planet', 'Знак', 'Накшатра', 'Градус']])

    st.markdown("---")
    st.subheader("🔄 Текущие Лидеры Периода (АК / AmK)")
    ak_now = df.iloc[0]
    amk_now = df.iloc[1]
    
    c1, c2 = st.columns(2)
    c1.metric("Атма-карака (АК)", ak_now['Planet'])
    c2.metric("Аматья-карака (AmK)", amk_now['Planet'])
    
    st.write(f"**Детали АК:** {get_full_info(ak_now)}")
    st.write(f"**Детали AmK:** {get_full_info(amk_now)}")

with tab2:
    st.header("📅 Расписание смены Карак на неделю")
    
    @st.cache_data(ttl=3600)
    def generate_plan():
        now_ref = datetime.utcnow() + timedelta(hours=3)
        monday = now_ref - timedelta(days=now_ref.weekday())
        monday = monday.replace(hour=0, minute=0, second=0)
        events, last_pair = [], ""
        
        # Проверка каждые 2 часа на протяжении 7 дней (168 часов)
        for h in range(0, 168, 2):
            ct = monday + timedelta(hours=h)
            t_w = ts.utc(ct.year, ct.month, ct.day, ct.hour-3, 0)
            df_w, _ = get_planet_data(t_w)
            curr_pair = f"{df_w.iloc[0]['Planet']}/{df_w.iloc[1]['Planet']}"
            
            if curr_pair != last_pair:
                events.append({
                    "Дата/Время (Сочи)": ct.strftime("%d.%m %H:00"),
                    "АК": get_full_info(df_w.iloc[0]),
                    "AmK": get_full_info(df_w.iloc[1])
                })
                last_pair = curr_pair
        return pd.DataFrame(events)

    if st.button('🗓️ Сформировать/Обновить расписание'):
        df_plan = generate_plan()
        df_plan.index = df_plan.index + 1
        st.table(df_plan)
        
    components.html("""
        <script>function pr(){window.print();}</script>
        <button onclick='pr()' style='width:100%; height:45px; background:#6A5ACD; color:white; border:none; border-radius:10px; cursor:pointer; font-weight:bold;'>🖨 ПЕЧАТЬ ПЛАНА</button>
    """, height=60)
