import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta, time
import pandas as pd
import math
import base64

# --- 1. CONFIG & ENGINE ---
st.set_page_config(page_title="Julia Assistant PRO", layout="wide")

@st.cache_resource
def init_engine():
    ts = load.timescale()
    eph = load('de421.bsp')
    return ts, eph

ts, eph = init_engine()

# --- 2. DICTIONARIES ---
P_ICONS = {'Sun': '☀️ Sun', 'Moon': '🌙 Moon', 'Mars': '🔴 Mars', 'Mercury': '☿️ Merc', 'Jupiter': '🔵 Jup', 'Venus': '♀️ Venus', 'Saturn': '🪐 Sat'}
Z_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]
NAK_LORDS = ["Кету", "Венера", "Солнце", "Луна", "Марс", "Раху", "Юпитер", "Сатурн", "Меркурий"] * 3

# --- 3. CORE MATH ---
def get_ayanamsa(t):
    T = (t.tt - 2451545.0) / 36525.0
    return 23.856235 + (2.30142 * T) + (0.000139 * T**2)

def calculate_astro(t):
    ayan = get_ayanamsa(t)
    earth = eph['earth']
    data = []
    
    # Планеты
    for name, obj in {'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 'Mercury': eph['mercury'], 'Jupiter': eph['jupiter_barycenter'], 'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']}.items():
        lon = (earth.at(t).observe(obj).ecliptic_latlon()[1].degrees - ayan) % 360
        nak_idx = int(lon / (360/27)) % 27
        data.append({
            'Planet': P_ICONS.get(name, name),
            'Sign': Z_SIGNS[int(lon/30)],
            'Nakshatra': f"{NAKSHATRAS[nak_idx]} ({NAK_LORDS[nak_idx]})",
            'Deg': lon % 30,
            'FullLon': lon
        })
    
    df = pd.DataFrame(data).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    df.insert(0, 'Role', ['AK', 'AmK', 'BK', 'MK', 'PiK', 'GK', 'DK'][:7])
    
    # Раху
    m_lon = earth.at(t).observe(eph['moon']).ecliptic_latlon()[1].degrees
    ra_lon = (m_lon - ayan + 180) % 360
    ra_deg = 30 - (ra_lon % 30)
    
    # Луна
    s_lon = earth.at(t).observe(eph['sun']).ecliptic_latlon()[1].degrees
    diff = (m_lon - s_lon) % 360
    tithi = math.ceil(diff / 12) or 1
    
    return df, ra_deg, tithi, "Шукла (Растущая)" if diff < 180 else "Кришна (Убывающая)"

# --- 4. UI COMPONENTS ---
def draw_rahu_monitor(deg):
    if deg < 2 or deg > 28: color, label = "#FF4B4B", "ГАНДАНТА (ХАОС)"
    elif deg < 5 or deg > 25: color, label = "#FFA500", "ВНИМАНИЕ (РИСК)"
    else: color, label = "#00C853", "ТЕХНИЧНАЯ ЗОНА"
    
    st.markdown(f"""
        <div style="background-color:{color}22; border: 1px solid {color}; padding: 20px; border-radius: 10px; text-align: center;">
            <h1 style="color:{color}; margin:0;">🐲 Раху: {deg:.2f}°</h1>
            <p style="color:{color}; font-weight: bold; margin:0;">{label}</p>
        </div>
    """, unsafe_allow_html=True)

# --- 5. MAIN APP ---
try:
    now_utc = datetime.utcnow()
    t_now = ts.utc(now_utc.year, now_utc.month, now_utc.day, now_utc.hour, now_utc.minute, now_utc.second)
    df_main, ra_val, tithi_val, phase_val = calculate_astro(t_now)

    tab1, tab2 = st.tabs(["💎 ПРЯМОЙ ЭФИР", "📅 ПЛАНИРОВЩИК"])

    with tab1:
        draw_rahu_monitor(ra_val)
        st.write("")
        
        # Инфо-панель
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("🌙 Лунный цикл", f"{tithi_val} день", phase_val)
        with col2:
            st.metric("💎 Текущая АК", df_main.iloc[0]['Planet'], f"{df_main.iloc[0]['Deg']:.2f}°")
        with col3:
            st.metric("🥈 Текущая AmK", df_main.iloc[1]['Planet'], f"{df_main.iloc[1]['Deg']:.2f}°")

        st.divider()
        
        # Основная таблица
        st.subheader("📊 Анализ Чара-карак")
        st.dataframe(df_main[['Role', 'Planet', 'Sign', 'Nakshatra', 'Deg']], width=None, hide_index=True)
        
        # Прогноз смены
        st.divider()
        st.subheader("🔄 Ближайшее изменение эфира")
        ak_name, amk_name = df_main.iloc[0]['Planet'], df_main.iloc[1]['Planet']
        
        for m in range(5, 1440, 5):
            t_f = now_utc + timedelta(minutes=m)
            ts_f = ts.utc(t_f.year, t_f.month, t_f.day, t_f.hour, t_f.minute)
            df_f, _, _, _ = calculate_astro(ts_f)
            if df_f.iloc[0]['Planet'] != ak_name or df_f.iloc[1]['Planet'] != amk_name:
                st.success(f"Следующая ротация через **{m} минут** (около {(t_f + timedelta(hours=3)).strftime('%H:%M')} МСК)")
                st.write(f"Новая конфигурация: **АК {df_f.iloc[0]['Planet']} / AmK {df_f.iloc[1]['Planet']}**")
                break

    with tab2:
        st.header("📅 Генератор плана ротаций")
        c_p1, c_p2 = st.columns(2)
        d_start = c_p1.date_input("Дата начала", datetime.now())
        d_end = c_p2.date_input("Дата окончания", datetime.now() + timedelta(days=3))
        
        if st.button("🚀 Сформировать отчет"):
            progress = st.progress(0)
            curr = datetime.combine(d_start, time(0,0)) - timedelta(hours=3)
            stop = datetime.combine(d_end, time(23,59)) - timedelta(hours=3)
            
            log = []
            t_init = ts.utc(curr.year, curr.month, curr.day, curr.hour, curr.minute)
            df_i, _, _, _ = calculate_astro(t_init)
            last_pair = f"{df_i.iloc[0]['Planet']}{df_i.iloc[1]['Planet']}"
            
            log.append({"Время (МСК)": (curr + timedelta(hours=3)).strftime("%d.%m %H:%M"), "АК": df_i.iloc[0]['Planet'], "AmK": df_i.iloc[1]['Planet'], "Знак АК": df_i.iloc[0]['Sign']})
            
            total_steps = int((stop - curr).total_seconds() / 600)
            step = 0
            
            while curr < stop:
                curr += timedelta(minutes=10)
                t_s = ts.utc(curr.year, curr.month, curr.day, curr.hour, curr.minute)
                df_s, _, _, _ = calculate_astro(t_s)
                new_pair = f"{df_s.iloc[0]['Planet']}{df_s.iloc[1]['Planet']}"
                
                if new_pair != last_pair:
                    log.append({"Время (МСК)": (curr + timedelta(hours=3)).strftime("%d.%m %H:%M"), "АК": df_s.iloc[0]['Planet'], "AmK": df_s.iloc[1]['Planet'], "Знак АК": df_s.iloc[0]['Sign']})
                    last_pair = new_pair
                
                step += 1
                if step % 20 == 0: progress.progress(min(step/total_steps, 1.0))
            
            progress.empty()
            st.table(pd.DataFrame(log))

except Exception as e:
    st.error(f"Системный сбой: {e}")
