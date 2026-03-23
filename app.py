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
    eph = load('de421.bsp')
    return ts, eph

ts, eph = init_engine()

# --- Константы и Словари ---
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]

NAK_LORDS = [
    "Кету", "Венера", "Солнце", "Луна", "Марс", "Раху", "Юпитер", "Сатурн", "Меркурий",
    "Кету", "Венера", "Солнце", "Луна", "Марс", "Раху", "Юпитер", "Сатурн", "Меркурий",
    "Кету", "Венера", "Солнце", "Луна", "Марс", "Раху", "Юпитер", "Сатурн", "Меркурий"
]

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
    return 23.856235 + (2.30142 * T) + (0.000139 * T**2)

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
    ketu_row = pd.DataFrame([{'Planet': 'Ketu', 'Lon': ketu_lon, 'Deg': ketu_lon % 30, 'Role': '-'}])
    df = pd.concat([df, ketu_row], ignore_index=True)
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
    sign_name = ZODIAC_SIGNS[int(row['Lon'] / 30)]
    p = row['Planet']
    nak_name = NAKSHATRAS[nak_idx]
    nak_lord = NAK_LORDS[nak_idx]
    return f"{P_ICONS.get(p, p)} | {Z_ICONS.get(sign_name, sign_name)} | ☸️ {nak_name} ({nak_lord})"

# --- ИНТЕРФЕЙС ---

# Добавление ЛОГОТИПА
logo_url = "http://googleusercontent.com/image_generation_content/0"
col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
with col_l2:
    st.image(logo_url, use_container_width=True)

st.markdown("<h1 style='text-align: center; color: #6A5ACD; margin-top: -30px;'>Julia Assistant Astro Coordination Center</h1>", unsafe_allow_html=True)

components.html("""
    <div style="background: linear-gradient(90deg, #1a1a2e, #16213e); padding:15px; border-radius:15px; text-align:center; font-family: sans-serif; border: 1px solid #6A5ACD;">
        <h2 id="clock" style="margin:0; color:#E0E0E0; letter-spacing: 2px;">Загрузка...</h2>
        <p style="margin:0; color:#888; font-size: 0.9em;">Sochi Astro-Coordination Time (UTC+3)</p>
    </div>
    <script>
        function updateClock() {
            let d = new Date();
            let utc = d.getTime() + (d.getTimezoneOffset() * 60000);
            let sochi = new Date(utc + (3600000 * 3));
            document.getElementById('clock').innerHTML = sochi.toLocaleTimeString('ru-RU');
        }
        setInterval(updateClock, 1000); updateClock();
    </script>
""", height=110)

tab1, tab2 = st.tabs(["📊 Прямой эфир", "📅 План на неделю"])

with tab1:
    now = datetime.utcnow()
    t_now = ts.utc(now.year, now.month, now.day, now.hour, now.minute, now.second)
    df, ayan_val = get_planet_data(t_now)
    tithi, l_status, l_icon = get_lunar_info(t_now)

    st.markdown(f"""
    <div style="background: #fdfbff; border-left: 5px solid #6A5ACD; padding: 15px; border-radius: 10px; margin-bottom: 20px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
        <h3 style="margin:0; color: #4B0082;">{l_icon} Лунный цикл</h3>
        <p style="font-size: 1.1em; margin: 5px 0;"><b>Титхи:</b> {tithi} сутки | <b>Статус:</b> {l_status}</p>
    </div>
    """, unsafe_allow_html=True)

    st.info(f"ℹ️ **Айанамша Лахири:** {format_deg_to_min(ayan_val)}")
    
    df_v = df.copy()
    df_v['Знак'] = df_v['Lon'].apply(lambda x: Z_ICONS[ZODIAC_SIGNS[int(x/30)]])
    
    def format_nak(lon):
        idx = int(lon / (360/27)) % 27
        return f"{NAKSHATRAS[idx]} ({NAK_LORDS[idx]})"
    
    df_v['Накшатра (Лорд)'] = df_v['Lon'].apply(format_nak)
    df_v['Градус'] = df_v['Deg'].apply(lambda x: f"{x:.4f}°")
    
    st.table(df_v[['Role', 'Planet', 'Знак', 'Накшатра (Лорд)', 'Градус']])

    st.markdown("---")
    st.subheader("🚀 Мониторинг ротаций (АК / AmK)")
    
    ak_now, am
