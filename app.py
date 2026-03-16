import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd
import time
import streamlit.components.v1 as components

# 1. Настройка
st.set_page_config(page_title="Max Pro-Trader CC", layout="wide")
st.markdown("<h1 style='text-align: center;'>Max Pro-Trader Coordination center</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>v5.6 Risk Map | XAU/USD | Сочи (UTC+3)</p>", unsafe_allow_html=True)

# Константы и логика риска
LAHIRI_AYANAMSA = 24.2255
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]

# Опасные накшатры для золота
DANGER_NAKS = ["Аридра", "Ашлеша", "Джьештха", "Мула", "Шатабхиша", "Пурва-бх"]
SAFE_NAKS = ["Пушья", "Рохини", "Уттара-пх", "Уттара-аш", "Хаста"]

def get_risk_color(nak_name):
    if nak_name in DANGER_NAKS: return "🔴 Опасно"
    if nak_name in SAFE_NAKS: return "🟢 Спокойно"
    return "🟡 Внимание"

def get_planet_data(t, eph):
    planets = {'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 'Mercury': eph['mercury'], 
               'Jupiter': eph['jupiter_barycenter'], 'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']}
    res = []
    for name, obj in planets.items():
        lon = (eph['earth'].at(t).observe(obj).ecliptic_latlon()[1].degrees - LAHIRI_AYANAMSA) % 360
        res.append({'Planet': name, 'Lon': lon, 'Deg': lon % 30})
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    df.index += 1
    df['Role'] = ['AK', 'AmK', 'BK', 'MK', 'PK', 'GK', 'DK']
    return df

def format_info(row):
    nak = NAKSHATRAS[int(row['Lon'] / (360/27)) % 27]
    return f"{row['Planet']} ({nak})", nak

ts = load.timescale()
eph = load('de421.bsp')

tab1, tab2 = st.tabs(["📊 Терминал", "📅 Карта Рисков (Юля)"])

with tab2:
    st.subheader("Еженедельный график опасных зон (XAU/USD)")
    now_ref = datetime.utcnow() + timedelta(hours=3)
    start_monday = now_ref - timedelta(days=now_ref.weekday())
    start_monday = start_monday.replace(hour=2, minute=0, second=0)
    
    weekly_data = []
    last_p = ""
    for h in range(0, 120, 2): # Шаг 2 часа для точности карты
        check_t = start_monday + timedelta(hours=h)
        if check_t.weekday() > 4: break
        
        t_w = ts.utc(check_t.year, check_t.month, check_t.day, check_t.hour-3, check_t.minute)
        df_w = get_planet_data(t_w, eph)
        ak_w, amk_w = df_w.iloc[0], df_w.iloc[1]
        nak_name = NAKSHATRAS[int(ak_w['Lon'] / (360/27)) % 27]
        
        curr_p = f"{ak_w['Planet']}-{amk_w['Planet']}"
        if curr_p != last_p:
            weekly_data.append({
                "Время": check_t.strftime("%d.%m %H:%M"),
                "Статус": get_risk_color(nak_name),
                "Пара AK/AmK": f"AK: {format_info(ak_w)[0]} | AmK: {format_info(amk_w)[0]}",
                "Юля / Max": "________________"
            })
            last_p = curr_p

    st.table(pd.DataFrame(weekly_data))
    components.html("<script>function pr(){window.print();}</script><button onclick='pr()' style='width:100%; height:40px; background:#4CAF50; color:white; border:none; border-radius:10px; cursor:pointer;'>🖨 ПЕЧАТЬ КАРТЫ РИСКОВ</button>", height=50)

with tab1:
    placeholder = st.empty()
    while True:
        c_now = datetime.utcnow() + timedelta(hours=3)
        t_c = ts.utc(c_now.year, c_now.month, c_now.day, c_now.hour-3, c_now.minute, c_now.second)
        df = get_planet_data(t_c, eph)
        ak = df.iloc[0]
        nak_name = NAKSHATRAS[int(ak['Lon'] / (360/27)) % 27]

        with placeholder.container():
            st.write(f"### 🕒 Сочи: {c_now.strftime('%H:%M:%S')}")
            
            # Визуальный индикатор риска на главной
            risk_status = get_risk_color(nak_name)
            if "🔴" in risk_status: st.error(f"ТЕКУЩИЙ СТАТУС: {risk_status} — Будьте предельно осторожны с Золотом!")
            elif "🟢" in risk_status: st.success(f"ТЕКУЩИЙ СТАТУС: {risk_status} — Благоприятный фон для трендов.")
            else: st.warning(f"ТЕКУЩИЙ СТАТУС: {risk_status} — Возможна волатильность.")

            df_v = df.copy()
            df_v['Знак'] = df_v['Lon'].apply(lambda x: ZODIAC_SIGNS[int(x/30)])
            df_v['Накшатра'] = df_v['Lon'].apply(lambda x: NAKSHATRAS[int(x/(360/27)) % 27])
            st.table(df_v[['Role', 'Planet', 'Знак', 'Накшатра', 'Deg']])
            
        time.sleep(1)
