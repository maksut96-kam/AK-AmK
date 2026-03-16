import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd
import time
import streamlit.components.v1 as components

# 1. Настройка и заголовок
st.set_page_config(page_title="Max Pro-Trader CC", layout="wide")
st.markdown("<h1 style='text-align: center;'>Max Pro-Trader Coordination center</h1>", unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: gray;'>v5.1 Stable | Цель: XAU/USD | Owner: Max</p>", unsafe_allow_html=True)

# Константы
LAHIRI_AYANAMSA = 24.2255
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]

# Полная база стратегий для Золота (27 Накшатр)
GOLD_STRATEGIES = {
    "Ашвини": "🔥 Импульс. Быстрый вход, золото может идти без ретеста.",
    "Бхарани": "⏳ Давление. Ожидайте накопления перед мощным выходом.",
    "Криттика": "🔪 Прорыв. Агрессивная работа по уровням.",
    "Рохини": "📈 Бычий тренд. Стабильный рост и ликвидность.",
    "Мригашира": "🔍 Разведка. Колебания цены, поиск направления.",
    "Аридра": "⛈ Хаос. Паника, резкие 'шпильки' на новостях.",
    "Пунарвасу": "🔄 Отскок. Возврат к средним значениям после движения.",
    "Пушья": "💎 Надежность. Сильный тренд, время для крупных позиций.",
    "Ашлеша": "🐍 Ловушка. Ложные пробои, маркетмейкеры снимают стопы.",
    "Магха": "🏛 Сила. Влияние институциональных объемов.",
    "Пурва-пх": "⏸ Пауза. Флет, затишье перед бурей.",
    "Уттара-пх": "✅ Уверенность. Продолжение текущего тренда.",
    "Хаста": "🛠 Техничность. Идеальная отработка уровней Фибоначчи.",
    "Читра": "📐 Структура. Формирование четких графических паттернов.",
    "Свати": "💨 Ветер. Высокая волатильность, неопределенность.",
    "Вишакха": "🎯 Цель. Рынок определился с вектором на ближайшие часы.",
    "Анурадха": "🛡 Поддержка. Скрытый набор позиций крупным игроком.",
    "Джьештха": "⚠️ Пик. Критическая точка, возможен резкий разворот.",
    "Мула": "🧨 Крах. Подрыв уровней, риск глубокого обвала.",
    "Пурва-аш": "🌅 Оптимизм. Рост ожиданий, золото в фазе накопления.",
    "Уттара-аш": "🏆 Победа. Завершение формирования тренда.",
    "Шравана": "👂 Инсайд. Движения на слухах и закрытой информации.",
    "Дхаништха": "🥁 Импульс. Ритмичные вливания объемов в стакан.",
    "Шатабхиша": "🔮 Манипуляция. Скрытые действия против толпы.",
    "Пурва-бх": "🧨 Риск. Высокое напряжение, готовность к срыву.",
    "Уттара-бх": "🌊 Глубина. Медленный, но мощный поток ликвидности.",
    "Ревати": "🔚 Финал. Завершение цикла, фиксация прибыли."
}

def get_nakshatra(lon):
    idx = int(lon / (360/27)) % 27
    names = list(GOLD_STRATEGIES.keys())
    return names[idx]

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

# Вкладки интерфейса
tab1, tab2 = st.tabs(["📊 Прямой эфир (Real-time)", "📅 Координация с Юлей (Неделя)"])

with tab1:
    placeholder = st.empty()
    ts = load.timescale()
    eph = load('de421.bsp')
    
    while True:
        now = datetime.utcnow() + timedelta(hours=3)
        t_now = ts.utc(now.year, now.month, now.day, now.hour, now.minute, now.second)
        df = get_planet_data(t_now, eph)
        ak, amk = df.iloc[0], df.iloc[1]
        ak_nak = get_nakshatra(ak['Lon'])
        
        with placeholder.container():
            st.write(f"### 🕒 Сочи: {now.strftime('%H:%M:%S')}")
            
            # Таблица
            df_view = df.copy()
            df_view['Знак'] = df_view['Lon'].apply(lambda x: ZODIAC_SIGNS[int(x/30)])
            df_view['Накшатра'] = df_view['Lon'].apply(get_nakshatra)
            st.table(df_view[['Role', 'Planet', 'Знак', 'Накшатра', 'Deg']])
            
            # Аналитика
            st.subheader("🎙 Голос Звезд: Анализ XAU/USD")
            st.info(f"**Атмакарака (Психология):** {ak['Planet']} в {ak_nak}. \n\n**Стратегия:** {GOLD_STRATEGIES[ak_nak]}")
            st.warning(f"**Аматьякарака (Инструменты):** {amk['Planet']} помогает реализовать цели через энергию {get_nakshatra(amk['Lon'])}.")
            
        time.sleep(1)

with tab2:
    st.subheader("Еженедельный план координации")
    ts_w, eph_w = load.timescale(), load('de421.bsp')
    base = datetime.utcnow() + timedelta(hours=3)
    
    weekly_data = []
    for i in range(7):
        d = base + timedelta(days=i)
        tw = ts_w.utc(d.year, d.month, d.day, 12, 0)
        dfw = get_planet_data(tw, eph_w)
        akw, amkw = dfw.iloc[0], dfw.iloc[1]
        nakw = get_nakshatra(akw['Lon'])
        
        weekly_data.append({
            "Дата": d.strftime("%d.%m"),
            "Пара AK/AmK": f"{akw['Planet']} / {amkw['Planet']}",
            "Накшатра AK": nakw,
            "Торговый контекст": GOLD_STRATEGIES[nakw],
            "Прогноз Max/Юля": "________________"
        })
    
    st.table(pd.DataFrame(weekly_data).set_index(pd.Index(range(1, 8))))
    
    components.html("""
        <script>function printPage() { window.print(); }</script>
        <button onclick="printPage()" style="width:100%; height:50px; background:#4CAF50; color:white; border:none; border-radius:10px; cursor:pointer; font-weight:bold;">
            🖨 ПЕЧАТЬ ПЛАНА (CTRL+P)
        </button>
    """, height=70)
