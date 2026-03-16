import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd

st.set_page_config(page_title="Sochi Trading Stars", layout="wide")

# Словарь знаков Зодиака
ZODIAC_SIGNS = [
    "Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", 
    "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"
]

def get_zodiac_sign(degrees):
    return ZODIAC_SIGNS[int(degrees / 30)]

def get_karakas(dt_input):
    ts = load.timescale()
    eph = load('de421.bsp')
    
    # dt_input уже приходит в сочинском времени (UTC+3)
    # Для расчетов Skyfield нам нужно передать "чистое" UTC
    utc_time = dt_input - timedelta(hours=3)
    t = ts.utc(utc_time.year, utc_time.month, utc_time.day, utc_time.hour, utc_time.minute)
    
    planets = {
        'Sun': eph['sun'], 'Mars': eph['mars'], 'Mercury': eph['mercury'],
        'Jupiter': eph['jupiter_barycenter'], 'Venus': eph['venus'], 
        'Saturn': eph['saturn_barycenter'], 'Moon': eph['moon']
    }
    
    data = []
    for name, obj in planets.items():
        total_lon = eph['earth'].at(t).observe(obj).ecliptic_latlon()[1].degrees
        deg_in_sign = total_lon % 30
        sign_name = get_zodiac_sign(total_lon)
        data.append({'Planet': name, 'Deg': round(deg_in_sign, 4), 'Sign': sign_name})
    
    df_sorted = pd.DataFrame(data).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    karaka_names = ['Atmakaraka (AK)', 'Amatyakaraka (AmK)', 'Bhratrukaraka (BK)', 
                    'Matrukaraka (MK)', 'Putrakaraka (PK)', 'Gnatikaraka (GK)', 'Darakaraka (DK)']
    
    df_sorted['Role'] = karaka_names
    return df_sorted

st.title("🛰 Real-time Анализ Карак (Сочи UTC+3)")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Настройки")
    use_current = st.checkbox("Использовать текущее время Сочи", value=True)
    
    if use_current:
        # Принудительно корректируем время сервера под Сочи
        calc_dt = datetime.utcnow() + timedelta(hours=3)
    else:
        d = st.date_input("Дата", datetime.now() + timedelta(hours=3))
        t = st.time_input("Время (Сочи)", (datetime.now() + timedelta(hours=3)).time())
        calc_dt = datetime.combine(d, t)
    
    st.success(f"Текущее время в Сочи: **{calc_dt.strftime('%H:%M:%S')}**")
    df_final = get_karakas(calc_dt)

with col2:
    st.subheader(f"Иерархия планет")
    st.dataframe(df_final[['Role', 'Planet', 'Sign', 'Deg']], use_container_width=True)

st.divider()
st.info("💡 Теперь время синхронизировано. Если AK (Атмакарака) меняется в течение дня — это сигнал к возможному развороту тренда.")
