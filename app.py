import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd
import time

st.set_page_config(page_title="Jyotish OS: Owner Edition", layout="wide")

# Константы
LAHIRI_AYANAMSA = 24.2255
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]

# Полный список 27 накшатр с характеристиками для трейдинга
NAKSHATRAS_DB = [
    ("Ашвини", "Кету", "Импульсивность, быстрый старт тренда"),
    ("Бхарани", "Венера", "Напряжение, фиксация прибыли"),
    ("Криттика", "Солнце", "Резкое пробитие уровней"),
    ("Рохини", "Луна", "Стабильный рост, ликвидность"),
    ("Мригашира", "Марс", "Поиск направления, волатильность"),
    ("Аридра", "Раху", "Хаос, неожиданные новости, паника"),
    ("Пунарвасу", "Юпитер", "Возврат к уровням, отскок"),
    ("Пушья", "Сатурн", "Медленный, надежный тренд"),
    ("Ашлеша", "Меркурий", "Коварные движения, ложные пробои"),
    ("Магха", "Кету", "Влияние старых институционалов"),
    ("Пурва-пхалгуни", "Венера", "Затишье, накопление сил"),
    ("Уттара-пхалгуни", "Солнце", "Уверенное продолжение движения"),
    ("Хаста", "Луна", "Детальная проработка уровней"),
    ("Читра", "Марс", "Структурность, четкие паттерны"),
    ("Свати", "Раху", "Рассеивание внимания, неопределенность"),
    ("Вишакха", "Юпитер", "Смена приоритетов в секторе"),
    ("Анурадха", "Сатурн", "Скрытая поддержка тренда"),
    ("Джьештха", "Меркурий", "Пик тренда, критическое мастерство"),
    ("Мула", "Кету", "Подрыв фундамента, обвал"),
    ("Пурва-ашадха", "Венера", "Ожидание прибыли, оптимизм"),
    ("Уттара-ашадха", "Солнце", "Окончательная победа быков/медведей"),
    ("Шравана", "Луна", "Слухи, инсайды, информационный поток"),
    ("Дхаништха", "Марс", "Ритмичные импульсы, объемы"),
    ("Шатабхиша", "Раху", "Скрытые манипуляции, 'черный лебедь'"),
    ("Пурва-бхадрапада", "Юпитер", "Стремление к цели любой ценой"),
    ("Уттара-бхадрапада", "Сатурн", "Глубокая консолидация"),
    ("Ревати", "Меркурий", "Завершение цикла, выход из позиций")
]

def get_nakshatra_info(lon):
    idx = int(lon / (360/27)) % 27
    return NAKSHATRAS_DB[idx]

def get_data():
    ts = load.timescale()
    eph = load('de421.bsp')
    now_sochi = datetime.utcnow() + timedelta(hours=3)
    
    # Расчет текущего и будущего времени для скоростей
    t1 = ts.utc(now_sochi.year, now_sochi.month, now_sochi.day, now_sochi.hour, now_sochi.minute, now_sochi.second)
    t2 = ts.utc(now_sochi.year, now_sochi.month, now_sochi.day, now_sochi.hour, now_sochi.minute, now_sochi.second + 3600) # +1 час
    
    planets_map = {'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 'Mercury': eph['mercury'], 
                   'Jupiter': eph['jupiter_barycenter'], 'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']}
    
    res = []
    for name, obj in planets_map.items():
        lon1 = (eph['earth'].at(t1).observe(obj).ecliptic_latlon()[1].degrees - LAHIRI_AYANAMSA) % 360
        lon2 = (eph['earth'].at(t2).observe(obj).ecliptic_latlon()[1].degrees - LAHIRI_AYANAMSA) % 360
        
        speed = (lon2 - lon1) # Градусов в час
        if speed > 180: speed -= 360
        if speed < -180: speed += 360
        
        nak_name, nak_lord, nak_desc = get_nakshatra_info(lon1)
        
        res.append({
            'Planet': f"{name} {'(R)' if speed < 0 else ''}",
            'Sign': ZODIAC_SIGNS[int(lon1 / 30)],
            'Deg': lon1 % 30,
            'Nakshatra': nak_name,
            'Nak_Desc': nak_desc,
            'Speed': speed
        })
    
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    df.index += 1
    df['Role'] = ['AK', 'AmK', 'BK', 'MK', 'PK', 'GK', 'DK']
    return df, now_sochi

st.title("🛰 Jyotish OS v4.6 — Command Center")

placeholder = st.empty()

while True:
    df, time_now = get_data()
    ak = df.iloc[0]
    amk = df.iloc[1]
    
    # Расчет времени до смены (в часах)
    deg_diff = ak['Deg'] - amk['Deg']
    speed_diff = amk['Speed'] - ak['Speed']
    time_to_swap = deg_diff / speed_diff if speed_diff > 0 else 0
    
    with placeholder.container():
        st.write(f"### 🕒 Sochi Time: {time_now.strftime('%H:%M:%S')}")
        
        # Информационная панель
        c1, c2, c3 = st.columns(3)
        c1.metric("Distance AK-AmK", f"{round(deg_diff, 4)}°")
        if time_to_swap > 0:
            c2.metric("Time to Swap", f"{round(time_to_swap, 1)} h")
        else:
            c2.info("AK is leading")
        c3.metric("Current AK", ak['Planet'])

        # Главная таблица
        st.subheader("Planetary Hierarchy (Real-time)")
        st.dataframe(df[['Role', 'Planet', 'Sign', 'Deg', 'Nakshatra']], use_container_width=True)

        # Секция для печати
        with st.expander("🖨 Отчет для печати (Print View)"):
            st.markdown("### Daily Trading Plan")
            st.table(df[['Role', 'Planet', 'Sign', 'Deg', 'Nakshatra']])
            st.button("Print Dashboard (Ctrl+P)")

        # Голос планет
        st.subheader("🎙 Voice of the Stars")
        st.success(f"**Атмакарака {ak['Planet']} в {ak['Nakshatra']}:** {ak['Nak_Desc']}. "
                   f"Это доминирующая сила текущего цикла в знаке {ak['Sign']}.")

    time.sleep(1)
