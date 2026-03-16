import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd
import streamlit.components.v1 as components

# 1. Настройки системы
st.set_page_config(page_title="Max Pro-Trader CC", layout="wide")

@st.cache_resource
def init_engine():
    return load.timescale(), load('de421.bsp')

ts, eph = init_engine()
LAHIRI_AYANAMSA = 24.2255
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]

def check_gandanta(lon):
    threshold = 3.333
    for junction in [0, 120, 240, 360]:
        if abs(lon - junction) <= threshold: return True
    return False

def get_planet_data(t):
    planets = {'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 'Mercury': eph['mercury'], 
               'Jupiter': eph['jupiter_barycenter'], 'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']}
    res = []
    for name, obj in planets.items():
        lon = (eph['earth'].at(t).observe(obj).ecliptic_latlon()[1].degrees - LAHIRI_AYANAMSA) % 360
        res.append({'Planet': name, 'Lon': lon, 'Deg': round(lon % 30, 4), 'IsGandanta': check_gandanta(lon)})
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    df.index += 1
    roles = ['AK', 'AmK', 'BK', 'MK', 'PK', 'GK', 'DK']
    df['Role'] = [roles[i] + (" ⚠️ Узел" if df.iloc[i]['IsGandanta'] else "") for i in range(len(roles))]
    return df

def format_info(row):
    nak = NAKSHATRAS[int(row['Lon'] / (360/27)) % 27]
    sign = ZODIAC_SIGNS[int(row['Lon'] / 30)]
    return f"{row['Planet']} ({sign}, {nak})"

# --- ИНТЕРФЕЙС ---
st.title("Max Pro-Trader Coordination center")

# Боковая панель для полной изоляции
menu = st.sidebar.selectbox("МЕНЮ", ["📊 ПРЯМОЙ ЭФИР", "📅 ПЛАН ДЛЯ ЮЛИ"])

if menu == "📊 ПРЯМОЙ ЭФИР":
    # Живое время без перезагрузки страницы
    components.html(f"""
        <div style="background:#1e1e1e; color:#00ff00; padding:20px; border-radius:10px; text-align:center; font-family:monospace;">
            <h1 id="clock" style="margin:0; font-size:40px;">00:00:00</h1>
            <p style="color:#aaa; margin:5px 0 0 0;">СОЧИ (UTC+3) | LIVE MODE</p>
        </div>
        <script>
            function update() {{
                let d = new Date();
                let utc = d.getTime() + (d.getTimezoneOffset() * 60000);
                let sochi = new Date(utc + (3600000 * 3));
                document.getElementById('clock').innerHTML = sochi.toLocaleTimeString();
            }}
            setInterval(update, 1000); update();
        </script>
    """, height=120)

    if st.button('🔄 ОБНОВИТЬ ДАННЫЕ ПЛАНЕТ'):
        now = datetime.utcnow() + timedelta(hours=3)
        t_now = ts.utc(now.year, now.month, now.day, now.hour-3, now.minute)
        df = get_planet_data(t_now)
        
        st.table(df[['Role', 'Planet', 'Deg']])
        
        st.markdown("---")
        st.subheader("🚀 Ближайшая ротация")
        ak_now, amk_now = df.iloc[0]['Planet'], df.iloc[1]['Planet']
        for m in range(1, 1440):
            t_f = ts.utc(now.year, now.month, now.day, now.hour-3, now.minute + m)
            df_f = get_planet_data(t_f)
            if df_f.iloc[0]['Planet'] != ak_now or df_f.iloc[1]['Planet'] != amk_now:
                st.success(f"📅 Смена через {m} мин: **{(now + timedelta(minutes=m)).strftime('%H:%M')}**")
                st.info(f"АК: {format_info(df_f.iloc[0])} | AmK: {format_info(df_f.iloc[1])}")
                break
    else:
        st.info("Нажмите кнопку выше, чтобы получить актуальные позиции планет.")

else:
    st.header("📅 План для Юли")
    if st.button('🚀 СГЕНЕРИРОВАТЬ ПЛАН НА НЕДЕЛЮ'):
        now_ref = datetime.utcnow() + timedelta(hours=3)
        start_mon = now_ref - timedelta(days=now_ref.weekday())
        start_mon = start_mon.replace(hour=2, minute=0, second=0)
        
        events, last_pair = [], ""
        with st.spinner("Идет расчет..."):
            for h in range(0, 125):
                base_time = start_mon + timedelta(hours=h)
                t_w = ts.utc(base_time.year, base_time.month, base_time.day, base_time.hour-3, 0)
                df_w = get_planet_data(t_w)
                pair_key = f"{df_w.iloc[0]['Planet']}-{df_w.iloc[1]['Planet']}"
                if pair_key != last_pair:
                    events.append({
                        "Время": base_time.strftime("%d.%m %H:%M"),
                        "АК": format_info(df_w.iloc[0]),
                        "AmK": format_info(df_w.iloc[1]),
                        "Ганданта": "⚠️" if (df_w.iloc[0]['IsGandanta'] or df_w.iloc[1]['IsGandanta']) else "✅"
                    })
                    last_pair = pair_key
        st.table(pd.DataFrame(events))
    else:
        st.warning("Для построения таблицы на неделю нажмите кнопку выше.")
