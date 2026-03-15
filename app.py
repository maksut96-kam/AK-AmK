import streamlit as st
from flatlib import const
from flatlib.chart import Chart
from flatlib.datetime import Datetime
from flatlib.geopos import Geopos
import pandas as pd
from datetime import datetime, timedelta

# Настройки страницы
st.set_page_config(page_title="AstroKarak Control", layout="wide", page_icon="🪐")

# Словарь иконок для наглядности
PLANET_ICONS = {
    'Sun': '☀️ Sun',
    'Moon': '🌙 Moon',
    'Mars': '🔴 Mars',
    'Mercury': '☿️ Merc',
    'Jupiter': '🤌 Jup',
    'Venus': '♀️ Venus',
    'Saturn': '🪐 Sat'
}

def get_karakas(dt_obj, lat, lon):
    d_str = dt_obj.strftime('%Y/%m/%d')
    t_str = dt_obj.strftime('%H:%M')
    dt = Datetime(d_str, t_str, '+00:00')
    pos = Geopos(lat, lon)
    # Используем Lahiri Ayanamsa по умолчанию
    chart = Chart(dt, pos, ID=const.LIST_SEVEN_PLANETS, ayanamsa=const.AYAN_LAHIRI)
    
    planets = []
    for p_id in const.LIST_SEVEN_PLANETS:
        p = chart.get(p_id)
        planets.append({'Planet': p_id, 'Degrees': round(p.lon % 30, 4)})
    
    # Сортировка: самая высокая степень — Атмакарака
    sorted_p = sorted(planets, key=lambda x: x['Degrees'], reverse=True)
    return sorted_p[0], sorted_p[1]

# --- ИНТЕРФЕЙС ---
st.title("🛰️ AstroKarak Control Panel v1.0")

with st.sidebar:
    st.header("Настройки системы")
    lat = st.number_input("Широта", value=55.75)
    lon = st.number_input("Долгота", value=37.62)
    st.info("Данные рассчитываются на 00:00 UTC для каждой даты.")

# Текущий расчет
now = datetime.now()
ak_now, amk_now = get_karakas(now, lat, lon)

# Главные индикаторы (Metrics)
col1, col2 = st.columns(2)
col1.metric("Atmakaraka (AK)", PLANET_ICONS.get(ak_now['Planet'], ak_now['Planet']), f"{ak_now['Degrees']}°")
col2.metric("Amatyakaraka (AmK)", PLANET_ICONS.get(amk_now['Planet'], amk_now['Planet']), f"{amk_now['Degrees']}°")

st.divider()

# Таблица на неделю
st.subheader("📅 Прогноз смены позиций (7 дней)")

data = []
prev_ak, prev_amk = None, None

for i in range(8):
    date_check = now + timedelta(days=i)
    ak, amk = get_karakas(date_check, lat, lon)
    
    # Пометка изменений (Change Detection)
    ak_display = PLANET_ICONS.get(ak['Planet'], ak['Planet'])
    amk_display = PLANET_ICONS.get(amk['Planet'], amk['Planet'])
    
    status = ""
    if prev_ak and ak['Planet'] != prev_ak: status += "🔄 AK CHANGED "
    if prev_amk and amk['Planet'] != prev_amk: status += "🔄 AmK CHANGED"
    
    data.append({
        "Дата": date_check.strftime('%d.%m (%a)'),
        "Atmakaraka": ak_display,
        "AK Deg": ak['Degrees'],
        "Amatyakaraka": amk_display,
        "AmK Deg": amk['Degrees'],
        "Событие": status
    })
    prev_ak, prev_amk = ak['Planet'], amk['Planet']

df = pd.DataFrame(data)

# Стилизация таблицы: подсвечиваем строки со сменой
def highlight_changes(row):
    return ['background-color: #1e3d33' if row['Событие'] != "" else '' for _ in row]

st.table(df)

st.caption("Система: 7 планет. Айанамша: Лахири. Расчет в реальном времени.")
