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

def get_karakas(dt_input, is_now=False):
    ts = load.timescale()
    eph = load('de421.bsp')
    
    # Корректируем время (если Сочи UTC+3, вычитаем 3 для получения UTC)
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
        data.append({'Planet': name, 'Deg': deg_in_sign, 'Sign': sign_name})
    
    # Сортировка по градусу для Карак
    df_sorted = pd.DataFrame(data).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    karaka_names = ['Atmakaraka (AK)', 'Amatyakaraka (AmK)', 'Bhratrukaraka (BK)', 
                    'Matrukaraka (MK)', 'Putrakaraka (PK)', 'Gnatikaraka (GK)', 'Darakaraka (DK)']
    
    df_sorted['Role'] = karaka_names
    return df_sorted, utc_time + timedelta(hours=3)

st.title("🛰 Real-time Анализ Карак (Сочи)")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Настройки времени")
    use_current = st.checkbox("Использовать текущее время", value=True)
    if not use_current:
        d = st.date_input("Дата", datetime.now())
        t = st.time_input("Время (Сочи)", datetime.now().time())
        calc_dt = datetime.combine(d, t)
    else:
        calc_dt = datetime.now()
    
    df_final, display_time = get_karakas(calc_dt)
    st.info(f"Расчет выполнен на: **{display_time.strftime('%H:%M:%S')}**")

with col2:
    st.subheader(f"Иерархия планет в знаках")
    # Красивый вывод таблицы
    st.dataframe(df_final[['Role', 'Planet', 'Sign', 'Deg']], use_container_width=True)

st.divider()
st.write("💡 **Для трейдинга:** Обрати внимание на 'Deg'. Если Атмакарака (AK) имеет градус > 29° или < 1°, планета находится в состоянии 'Мритью-бхага' или 'Ганданта' — это зоны экстремальной турбулентности на графиках.")
