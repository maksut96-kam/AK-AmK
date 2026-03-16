import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd
import time
import streamlit.components.v1 as components

# 1. Настройка и статический заголовок
st.set_page_config(page_title="Max Pro-Trader CC", layout="wide")
st.markdown("<h1 style='text-align: center;'>Max Pro-Trader Coordination center</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>v4.8 Build | System Area: Sochi (UTC+3)</p>", unsafe_allow_html=True)

# Константы (Накшатры)
LAHIRI_AYANAMSA = 24.2255
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS_DB = [
    ("Ашвини", "Кету", "Резкий старт"), ("Бхарани", "Венера", "Напряжение"), ("Криттика", "Солнце", "Прорыв"),
    ("Рохини", "Луна", "Рост"), ("Мригашира", "Марс", "Поиск"), ("Аридра", "Раху", "Хаос"),
    ("Пунарвасу", "Юпитер", "Отскок"), ("Пушья", "Сатурн", "Стабильность"), ("Ашлеша", "Меркурий", "Ловушка"),
    ("Магха", "Кету", "Традиция"), ("Пурва-пх", "Венера", "Пауза"), ("Уттара-пх", "Солнце", "Успех"),
    ("Хаста", "Луна", "Точность"), ("Читра", "Марс", "Структура"), ("Свати", "Раху", "Ветер"),
    ("Вишакха", "Юпитер", "Цель"), ("Анурадха", "Сатурн", "Скрытое"), ("Джьештха", "Меркурий", "Мастерство"),
    ("Мула", "Кету", "Корень/Крах"), ("Пурва-аш", "Венера", "Оптимизм"), ("Уттара-аш", "Солнце", "Победа"),
    ("Шравана", "Луна", "Инсайд"), ("Дхаништха", "Марс", "Импульс"), ("Шатабхиша", "Раху", "Манипуляция"),
    ("Пурва-бх", "Юпитер", "Жертва"), ("Уттара-бх", "Сатурн", "Глубина"), ("Ревати", "Меркурий", "Финал")
]

def get_planet_data(t, eph):
    planets = {'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 'Mercury': eph['mercury'], 
               'Jupiter': eph['jupiter_barycenter'], 'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']}
    res = []
    for name, obj in planets.items():
        lon = (eph['earth'].at(t).observe(obj).ecliptic_latlon()[1].degrees - LAHIRI_AYANAMSA) % 360
        res.append({'Planet': name, 'Lon': lon, 'Deg': lon % 30})
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    df.index += 1
    return df

# Вкладки
tab1, tab2 = st.tabs(["📊 Real-time Terminal", "📅 Weekly Strategy & Print"])

with tab1:
    placeholder = st.empty()
    ts = load.timescale()
    eph = load('de421.bsp')
    
    # Живой цикл
    while True:
        now_sochi = datetime.utcnow() + timedelta(hours=3)
        t_now = ts.utc(now_sochi.year, now_sochi.month, now_sochi.day, now_sochi.hour, now_sochi.minute, now_sochi.second)
        df_now = get_planet_data(t_now, eph)
        ak = df_now.iloc[0]
        nak_info = NAKSHATRAS_DB[int(ak['Lon'] / (360/27)) % 27]

        with placeholder.container():
            st.write(f"### 🕒 Sochi Time: {now_sochi.strftime('%H:%M:%S')}")
            st.dataframe(df_now[['Planet', 'Deg']], use_container_width=True)
            st.success(f"**AK {ak['Planet']} в {nak_info[0]}:** {nak_info[2]}")
        time.sleep(1)

with tab2:
    st.subheader("Weekly Coordination Plan")
    st.info("Распечатайте эту форму для совместной работы с Юлей.")
    
    # Генерация плана на 7 дней
    ts_w = load.timescale()
    eph_w = load('de421.bsp')
    base_date = datetime.utcnow() + timedelta(hours=3)
    weekly_list = []
    
    for i in range(7):
        day = base_date + timedelta(days=i)
        t_w = ts_w.utc(day.year, day.month, day.day, 12, 0) # Расчет на полдень
        df_w = get_planet_data(t_w, eph_w)
        ak_w = df_w.iloc[0]
        amk_w = df_w.iloc[1]
        nak_w = NAKSHATRAS_DB[int(ak_w['Lon'] / (360/27)) % 27]
        
        weekly_list.append({
            "Дата": day.strftime("%d.%m"),
            "Пара AK / AmK": f"{ak_w['Planet']} / {amk_w['Planet']}",
            "Накшатра AK": nak_w[0],
            "Характер периода": nak_w[2],
            "Прогноз (Max/Юля)": "________________" 
        })
    
    st.table(pd.DataFrame(weekly_list))

    # Кнопка печати через JS (вне цикла!)
    components.html("""
        <script>function printPage() { window.print(); }</script>
        <button onclick="printPage()" style="width:100%; height:50px; background:#4CAF50; color:white; border:none; border-radius:10px; cursor:pointer; font-weight:bold;">
            🖨 ОТПРАВИТЬ ПЛАН НА ПЕЧАТЬ (CTRL+P)
        </button>
    """, height=70)
