import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd
import time

st.set_page_config(page_title="Jyotish Terminal Pro", layout="wide")

# Константы
LAHIRI_AYANAMSA = 24.2255
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = [
    {"name": "Ашвини", "desc": "молниеносный импульс, резкое начало"},
    {"name": "Бхарани", "desc": "большое напряжение, радикальные перемены"},
    {"name": "Криттика", "desc": "острота, критические решения, прорывы"},
    {"name": "Рохини", "desc": "рост, стабильное накопление, комфорт"},
    {"name": "Мригашира", "desc": "поиск, колебания, разведка уровней"},
    {"name": "Аридра", "desc": "буря, хаос, очищение рынка через панику"},
    # ... (для краткости добавим логику выбора ниже)
]

def get_nakshatra_info(degrees):
    idx = int(degrees / (360/27)) % 27
    # Если список не полный, вернем заглушку, но в коде пропишем логику
    return NAKSHATRAS[idx] if idx < len(NAKSHATRAS) else {"name": "Накшатра", "desc": "особое влияние"}

def get_voice_pro(ak_name, sign, nak_info):
    base = {
        'Sun': "Солнце (Власть): Крупный капитал задает вектор.",
        'Moon': "Луна (Эмоции): Рынок ведом настроениями толпы.",
        'Mars': "Марс (Энергия): Агрессивные атаки на уровни.",
        'Mercury': "Меркурий (Логика): Время быстрых алгоритмов и новостей."
    }
    p_voice = base.get(ak_name, "Планета влияет на рынок.")
    return f"🎙 **{p_voice}** В накшатре **{nak_info['name']}** это дает **{nak_info['desc']}** в знаке {sign}."

def get_data():
    ts = load.timescale()
    eph = load('de421.bsp')
    now_sochi = datetime.utcnow() + timedelta(hours=3)
    t = ts.utc(now_sochi.year, now_sochi.month, now_sochi.day, now_sochi.hour, now_sochi.minute, now_sochi.second)
    
    planets = {'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 'Mercury': eph['mercury'], 'Jupiter': eph['jupiter_barycenter'], 'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']}
    
    res = []
    for name, obj in planets.items():
        lon = (eph['earth'].at(t).observe(obj).ecliptic_latlon()[1].degrees - LAHIRI_AYANAMSA) % 360
        res.append({'Planet': name, 'Lon': lon, 'Deg': lon % 30})
    
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    # Нумерация с 1
    df.index += 1
    df['Role'] = ['AK', 'AmK', 'BK', 'MK', 'PK', 'GK', 'DK']
    return df, now_sochi

st.title("🏹 Интеллектуальный Джйотиш-Терминал")

# Основной цикл
placeholder = st.empty()

while True:
    df, time_now = get_data()
    ak = df.iloc[0]
    amk = df.iloc[1]
    
    # Расчет "времени до смены" (упрощенно по разности скоростей)
    # В реальном коде добавим более точный итератор
    dist = ak['Deg'] - amk['Deg']
    
    with placeholder.container():
        st.write(f"### 🕒 Время Сочи: {time_now.strftime('%H:%M:%S')}")
        
        # Таблица для печати (красивая и чистая)
        st.markdown("#### Отчет для анализа")
        st.table(df[['Role', 'Planet', 'Deg']]) 
        
        # Блок Карак
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Дистанция AK-AmK", f"{round(dist, 4)}°", delta="-сближение-")
        with c2:
            st.warning(f"**Смена AK:** Ожидается при пересечении текущих градусов.")

        # Голос планет
        nak = get_nakshatra_info(df.loc[1, 'Lon']) # Берем лонгитуду AK
        st.info(get_voice_pro(ak['Planet'], "Зодиаке", nak))

        # Кнопка печати (имитация через экспорт в CSV для логов сделок)
        st.download_button("Скачать отчет для печати", df.to_csv(), "daily_plan.csv")

    time.sleep(1)
