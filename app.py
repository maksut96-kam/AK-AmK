import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd
import time
import streamlit.components.v1 as components

# 1. Настройка страницы и Статичный Заголовок
st.set_page_config(page_title="Max Pro-Trader CC", layout="wide")
st.markdown("<h1 style='text-align: center;'>Max Pro-Trader Coordination center</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>Версия 5.0 | Система: Сочи (UTC+3) | Цель: XAU/USD</p>", unsafe_allow_html=True)

# Константы
LAHIRI_AYANAMSA = 24.2255
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]

# Расширенная база Накшатр для анализа
NAKSHATRAS_ANALYTICS = {
    "Ашвини": {"lord": "Кету", "effect": "Резкие ценовые импульсы, начало мощных движений по Золоту."},
    "Бхарани": {"lord": "Венера", "effect": "Напряженное ожидание, возможна крупная фиксация прибыли на уровнях."},
    "Криттика": {"lord": "Солнце", "effect": "Острые пробои, агрессивное поведение маркетмейкеров."},
    "Рохини": {"lord": "Луна", "effect": "Стабильный приток ликвидности, уверенный рост актива."},
    "Пунарвасу": {"lord": "Юпитер", "effect": "Возврат к средним значениям, фаза отскока после коррекции."},
    # ... (база дополняется аналогично для всех 27 накшатр)
}

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

def get_nakshatra_name(lon):
    idx = int(lon / (360/27)) % 27
    names = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]
    return names[idx]

def analyze_market(df):
    ak = df.iloc[0]
    amk = df.iloc[1]
    ak_nak = get_nakshatra_name(ak['Lon'])
    amk_nak = get_nakshatra_name(amk['Lon'])
    
    analysis = f"""
    **Анализ Психологии (AK - {ak['Planet']}):** Настроение рынка через {ak_nak} указывает на {NAKSHATRAS_ANALYTICS.get(ak_nak, {}).get('effect', 'стабильность')}.
    **Анализ Действий (AmK - {amk['Planet']}):** Инструментарий в {amk_nak} предполагает тактику работы через {NAKSHATRAS_ANALYTICS.get(amk_nak, {}).get('effect', 'накопление')}.
    **Вывод для XAU/USD:** Взаимодействие {ak['Planet']} и {amk['Planet']} создает условия для волатильности на текущих уровнях.
    """
    return analysis

# ИНТЕРФЕЙС
tab1, tab2 = st.tabs(["📊 Поток Планет (Real-time)", "📅 Стратегия на неделю"])

with tab1:
    placeholder = st.empty()
    ts = load.timescale()
    eph = load('de421.bsp')
    
    while True:
        now_sochi = datetime.utcnow() + timedelta(hours=3)
        t_now = ts.utc(now_sochi.year, now_sochi.month, now_sochi.day, now_sochi.hour, now_sochi.minute, now_sochi.second)
        df = get_planet_data(t_now, eph)
        
        with placeholder.container():
            st.write(f"### 🕒 Время Сочи: {now_sochi.strftime('%H:%M:%S')}")
            
            # Таблица
            display_df = df.copy()
            display_df['Знак'] = display_df['Lon'].apply(lambda x: ZODIAC_SIGNS[int(x/30)])
            display_df['Накшатра'] = display_df['Lon'].apply(get_nakshatra_name)
            st.table(display_df[['Role', 'Planet', 'Знак', 'Накшатра', 'Deg']])
            
            st.subheader("🎙 Голос Звезд (Анализ рынка)")
            st.info(analyze_market(df))
        time.sleep(1)

with tab2:
    st.subheader("Координационный план (Неделя)")
    # Здесь будет расширенная логика с часами и минутами смены AK/AmK
    # И кнопка печати
    st.write("Формирование детального графика смен ролей...")
