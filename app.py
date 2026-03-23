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
    
    # Раху (инвертированный градус для карак)
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
    sign_idx = int(row['Lon'] / 30)
    p = row['Planet']
    return f"{P_ICONS.get(p, p)} | {Z_ICONS[sign_idx]} | ☸️ {NAKSHATRAS[nak_idx]}"

# --- ИНТЕРФЕЙС ---
st.markdown("<h1 style='text-align: center; color: #6A5ACD;'>✨ Julia Assistant Astro Coordination Center ✨</h1>", unsafe_allow_html=True)

components.html("""
    <div style="background: linear-gradient(90deg, #e0eafc, #cfdef3); padding:15px; border-radius:15px; text-align:center; font-family: sans-serif;">
        <h2 id="clock" style="margin:0; color:#4B0082;">Загрузка...</h2>
        <p style="margin:0; color:#555;">Sochi Time (UTC+3)</p>
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

    # Красивый виджет Луны
    st.markdown(f"""
    <div style="background: #fffafa; border-left: 5px solid #6A5ACD; padding: 15px; border-radius: 10px; margin-bottom: 20px;">
        <h3 style="margin:0;">{l_icon} Лунный цикл</h3>
        <p style="font-size: 1.1em; margin: 5px 0;"><b>Титхи:</b> {tithi} сутки | <b>Статус:</b> {l_status}</p>
    </div>
    """, unsafe_allow_html=True)

    st.info(f"ℹ️ **Айанамша Лахири:** {format_deg_to_min(ayan_val)}")
    
    df_v = df.copy()
    df_v['Знак'] = df_v['Lon'].apply(lambda x: Z_ICONS[int(x/30)])
    df_v['Накшатра'] = df_v['Lon'].apply(lambda x: NAKSHATRAS[int(x/(360/27)) % 27])
    df_v['Градус'] = df_v['Deg'].apply(lambda x: f"{x:.4f}°")
    st.table(df_v[['Role', 'Planet', 'Знак', 'Накшатра', 'Градус']])

    st.markdown("---")
    st.subheader("🚀 Мониторинг ротаций (АК / AmK)")
    
    ak_now, amk_now = df.iloc[0]['Planet'], df.iloc[1]['Planet']
    col1, col2 = st.columns(2)

    with col1:
        st.write("⬅️ **Предыдущая смена:**")
        found_prev = False
        for m in range(1, 2880, 10):
            past_time = now - timedelta(minutes=m)
            t_p = ts.utc(past_time.year, past_time.month, past_time.day, past_time.hour, past_time.minute)
            df_p, _ = get_planet_data(t_p)
            if df_p.iloc[0]['Planet'] != ak_now or df_p.iloc[1]['Planet'] != amk_now:
                st.warning(f"📅 {(past_time + timedelta(hours=3)).strftime('%d.%m %H:%M')}")
                st.write(f"**АК:** {get_full_info(df_p.iloc[0])}")
                st.write(f"**AmK:** {get_full_info(df_p.iloc[1])}")
                found_prev = True; break
        if not found_prev: st.write("Не найдено в пределах 48ч")

    with col2:
        st.write("➡️ **Следующая смена:**")
        found_next = False
        for m in range(1, 2880, 10):
            future_time = now + timedelta(minutes=m)
            t_f = ts.utc(future_time.year, future_time.month, future_time.day, future_time.hour, future_time.minute)
            df_f, _ = get_planet_data(t_f)
            if df_f.iloc[0]['Planet'] != ak_now or df_f.iloc[1]['Planet'] != amk_now:
                st.success(f"📅 {(future_time + timedelta(hours=3)).strftime('%d.%m %H:%M')}")
                st.write(f"**АК:** {get_full_info(df_f.iloc[0])}")
                st.write(f"**AmK:** {get_full_info(df_f.iloc[1])}")
                found_next = True; break
        if not found_next: st.write("Не найдено в пределах 48ч")

    st.markdown("---")
    st.info("💎 **Текущий активный период:**")
    c_ak, c_amk = st.columns(2)
    c_ak.metric("Текущая АК", get_full_info(df.iloc[0]))
    c_amk.metric("Текущая AmK", get_full_info(df.iloc[1]))

with tab2:
    st.header("Таймлайн на неделю")
    @st.cache_data(ttl=3600)
    def generate_plan():
        ref = datetime.utcnow() + timedelta(hours=3)
        start = ref - timedelta(days=ref.weekday()); start = start.replace(hour=0, minute=0)
        events, last_pair = [], ""
        for h in range(0, 168, 1):
            ct = start + timedelta(hours=h)
            t_w = ts.utc(ct.year, ct.month, ct.day, ct.hour-3, 0)
            df_w, _ = get_planet_data(t_w)
            pair = f"{df_w.iloc[0]['Planet']}/{df_w.iloc[1]['Planet']}"
            if pair != last_pair:
                events.append({"Дата/Время": ct.strftime("%d.%m %H:00"), "АК": get_full_info(df_w.iloc[0]), "AmK": get_full_info(df_w.iloc[1])})
                last_pair = pair
        return pd.DataFrame(events)

    if st.button('Сгенерировать план'):
        df_plan = generate_plan(); df_plan.index += 1
        st.table(df_plan)
        components.html("<script>function pr(){window.print();}</script><button onclick='pr()' style='width:100%; height:45px; background:#4CAF50; color:white; border:none; border-radius:10px; cursor:pointer;'>🖨 ПЕЧАТЬ ПЛАНА</button>", height=60)
