import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd
import time

st.set_page_config(page_title="Jyotish Pro Terminal", layout="wide")

# Константы
LAHIRI_AYANAMSA = 24.2255 # Уточненная на 2026 год
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = [
    "Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша",
    "Магха", "Пурва-пхалгуни", "Уттара-пхалгуни", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха",
    "Мула", "Пурва-ашадха", "Уттара-ашадха", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бхадрапада", "Уттара-бхадрапада", "Ревати"
]

def get_nakshatra(degrees):
    idx = int(degrees / (360/27))
    return NAKSHATRAS[idx % 27]

def get_voice_of_ak(ak_planet, sign):
    interpretations = {
        'Sun': f"AK Солнце в {sign}: Рынок под влиянием крупных государственных структур или лидеров индустрии. Время 'сильных' трендов.",
        'Moon': f"AK Луна в {sign}: Высокая эмоциональность масс. Ожидайте хаотичных движений и влияния новостного фона.",
        'Mars': f"AK Марс в {sign}: Агрессивные продажи или покупки. Импульсивные пробои уровней Фибоначчи.",
        'Mercury': f"AK Меркурий в {sign}: Время высокой активности скальперов и ботов. Множество мелких сделок.",
        'Jupiter': f"AK Юпитер в {sign}: Глобальные инвесторы ищут ценность. Позитивные ожидания и расширение рынка.",
        'Venus': f"AK Венера в {sign}: Период консолидации и поиска баланса. Рынок стремится к 'справедливой' цене.",
        'Saturn': f"AK Сатурн в {sign}: Жесткое давление, ограничения и затяжные коррекции. Время терпеливых трейдеров."
    }
    return interpretations.get(ak_planet, "Планеты шепчут... наблюдайте за графиком.")

def get_data():
    ts = load.timescale()
    eph = load('de421.bsp')
    now_sochi = datetime.utcnow() + timedelta(hours=3)
    
    # Расчет для двух моментов времени (сейчас и через секунду) для определения скорости
    t1 = ts.utc(now_sochi.year, now_sochi.month, now_sochi.day, now_sochi.hour, now_sochi.minute, now_sochi.second)
    t2 = ts.utc(now_sochi.year, now_sochi.month, now_sochi.day, now_sochi.hour, now_sochi.minute, now_sochi.second + 1)
    
    planets_map = {'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 'Mercury': eph['mercury'], 'Jupiter': eph['jupiter_barycenter'], 'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']}
    
    results = []
    for name, obj in planets_map.items():
        lon1 = (eph['earth'].at(t1).observe(obj).ecliptic_latlon()[1].degrees - LAHIRI_AYANAMSA) % 360
        lon2 = (eph['earth'].at(t2).observe(obj).ecliptic_latlon()[1].degrees - LAHIRI_AYANAMSA) % 360
        
        speed = lon2 - lon1
        # Учитываем переход через 0/360 градусов
        if speed > 180: speed -= 360
        if speed < -180: speed += 360
        
        deg_in_sign = lon1 % 30
        status = "(R)" if speed < 0 else ""
        
        results.append({
            'Planet': f"{name} {status}",
            'Sign': ZODIAC_SIGNS[int(lon1 / 30)],
            'Deg': round(deg_in_sign, 5),
            'Nakshatra': get_zodiac_sign_with_nakshatra(lon1)
        })
    
    df = pd.DataFrame(results).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    df['Role'] = ['AK', 'AmK', 'BK', 'MK', 'PK', 'GK', 'DK']
    return df, now_sochi

def get_zodiac_sign_with_nakshatra(lon):
    return get_nakshatra(lon)

st.title("🏹 Jyotish Pro-Trader Terminal (v4.0)")

placeholder = st.empty()

while True:
    df_live, time_now = get_data()
    ak_row = df_live.iloc[0]
    
    with placeholder.container():
        st.subheader(f"🕒 Сочи: {time_now.strftime('%H:%M:%S')}")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.dataframe(df_live[['Role', 'Planet', 'Sign', 'Deg', 'Nakshatra']], use_container_width=True)
        
        with col2:
            st.metric("Текущая Атмакарака", ak_row['Planet'])
            st.write(f"**Знак:** {ak_row['Sign']}")
            st.write(f"**Накшатра:** {ak_row['Nakshatra']}")

        st.subheader("🎙 Голос Планет")
        st.success(get_voice_of_ak(ak_row['Planet'].split()[0], ak_row['Sign']))
        
    time.sleep(1)
