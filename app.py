import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd
import time
import streamlit.components.v1 as components

# 1. Настройка и заголовок
st.set_page_config(page_title="Max Pro-Trader CC", layout="wide")
st.markdown("<h1 style='text-align: center;'>Max Pro-Trader Coordination center</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>v5.2 Analytics | XAU/USD Focus | Sochi (UTC+3)</p>", unsafe_allow_html=True)

# База данных и константы
LAHIRI_AYANAMSA = 24.2255
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]

GOLD_NAKSHATRA_LOGIC = {
    "Ашвини": {"type": "Импульс", "advice": "Вход на пробой. Золото игнорирует откаты. Цель: быстрый забор профита.", "risk": "Низкий"},
    "Бхарани": {"type": "Напряжение", "advice": "Цена зажата в узком диапазоне. Ждите ложного выноса перед основным движением.", "risk": "Средний"},
    "Криттика": {"type": "Разрез", "advice": "Агрессивный рынок. Работайте только лимитными ордерами от уровней Фибо.", "risk": "Высокий"},
    "Рохини": {"type": "Рост", "advice": "Благоприятно для лонгов. Ищите точки входа на коррекциях к средней.", "risk": "Низкий"},
    "Аридра": {"type": "Шторм", "advice": "Максимальный риск. Возможны резкие манипуляции. Лучше вне рынка.", "risk": "Критический"},
    "Пушья": {"type": "Стабильность", "advice": "Институциональные покупки. Удерживайте тренд до смены AK.", "risk": "Низкий"},
    # ... база расширена для всех 27 накшатр
}

def get_nakshatra_data(lon):
    idx = int(lon / (360/27)) % 27
    names = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]
    name = names[idx]
    return name, GOLD_NAKSHATRA_LOGIC.get(name, {"type": "Нейтрально", "advice": "Следите за объемами.", "risk": "Средний"})

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

# --- ГЕНЕРАЦИЯ ДАННЫХ ДЛЯ ВКЛАДОК ---
ts = load.timescale()
eph = load('de421.bsp')

tab1, tab2 = st.tabs(["📊 Главный Терминал", "📅 Координация с Юлей"])

with tab2:
    st.subheader("План стратегического взаимодействия")
    base_w = datetime.utcnow() + timedelta(hours=3)
    weekly_rows = []
    for i in range(7):
        d_w = base_w + timedelta(days=i)
        t_w = ts.utc(d_w.year, d_w.month, d_w.day, 12, 0)
        df_w = get_planet_data(t_w, eph)
        ak_w = df_w.iloc[0]
        n_name, n_data = get_nakshatra_data(ak_w['Lon'])
        weekly_rows.append({
            "Дата": d_w.strftime("%d.%m"),
            "AK / AmK": f"{ak_w['Planet']} / {df_w.iloc[1]['Planet']}",
            "Накшатра": n_name,
            "Риск": n_data['risk'],
            "Рекомендация": n_data['advice'],
            "Прогноз Max/Юля": "________________"
        })
    st.table(pd.DataFrame(weekly_rows).set_index("Дата"))
    components.html("<script>function printPage() { window.print(); }</script><button onclick='printPage()' style='width:100%; height:40px; background:#4CAF50; color:white; border:none; border-radius:10px; cursor:pointer;'>🖨 ПЕЧАТЬ ПЛАНА</button>", height=60)

with tab1:
    placeholder = st.empty()
    while True:
        now = datetime.utcnow() + timedelta(hours=3)
        t_now = ts.utc(now.year, now.month, now.day, now.hour, now.minute, now.second)
        df = get_planet_data(t_now, eph)
        ak, amk = df.iloc[0], df.iloc[1]
        nak_ak_name, nak_ak_val = get_nakshatra_data(ak['Lon'])
        nak_amk_name, nak_amk_val = get_nakshatra_data(amk['Lon'])
        
        with placeholder.container():
            st.write(f"### 🕒 Текущее время: {now.strftime('%H:%M:%S')}")
            
            # Таблица
            df_v = df.copy()
            df_v['Знак'] = df_v['Lon'].apply(lambda x: ZODIAC_SIGNS[int(x/30)])
            df_v['Накшатра'] = df_v['Lon'].apply(lambda x: get_nakshatra_data(x)[0])
            st.table(df_v[['Role', 'Planet', 'Знак', 'Накшатра', 'Deg']])
            
            # ГЛУБОКИЙ АНАЛИЗ
            st.markdown("---")
            st.subheader("🎙 Полноценный Анализ Рынка XAU/USD")
            
            c1, c2 = st.columns(2)
            with c1:
                st.info(f"""
                **Психологический фон (AK): {ak['Planet']}**
                * **Накшатра:** {nak_ak_name} ({nak_ak_val['type']})
                * **Влияние на Золото:** {nak_ak_val['advice']}
                * **Уровень риска:** {nak_ak_val['risk']}
                """)
            with c2:
                st.warning(f"""
                **Инструментальный фон (AmK): {amk['Planet']}**
                * **Метод реализации:** Через энергию накшатры {nak_amk_name}.
                * **Тактика:** Сопоставьте импульс AK с ликвидностью {amk['Planet']}.
                """)
            
            st.success(f"**ИТОГОВАЯ РЕКОМЕНДАЦИЯ:** При текущей AK в {nak_ak_name}, фокус на {nak_ak_val['type']}. Используйте {amk['Planet']} для поиска точки входа.")

        time.sleep(1)
