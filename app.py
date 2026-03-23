import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd
import streamlit.components.v1 as components
import math
import os
import base64

# 1. Системные настройки
st.set_page_config(page_title="Julia Assistant Astro", layout="wide")

@st.cache_resource
def init_engine():
    ts = load.timescale()
    # DE421 поддерживает период примерно с 1900 по 2050 годы
    eph = load('de421.bsp')
    return ts, eph

ts, eph = init_engine()

# --- Константы и Словари ---
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]
NAK_LORDS = ["Кету", "Венера", "Солнце", "Луна", "Марс", "Раху", "Юпитер", "Сатурн", "Меркурий"] * 3
P_ICONS = {'Sun': '☀️ Sun', 'Moon': '🌙 Moon', 'Mars': '🔴 Mars', 'Mercury': '☿️ Merc', 'Jupiter': '🔵 Jup', 'Venus': '♀️ Venus', 'Saturn': '🪐 Sat', 'Rahu': '🐲 Rahu', 'Ketu': '🐍 Ketu'}
Z_ICONS = {"Овен": "♈ Овен", "Телец": "♉ Телец", "Близнецы": "♊ Близн", "Рак": "♋ Рак", "Лев": "♌ Лев", "Дева": "♍ Дева", "Весы": "♎ Весы", "Скорпион": "♏ Скорп", "Стрелец": "♐ Стрел", "Козерог": "♑ Козег", "Водолей": "♒ Водол", "Рыбы": "♓ Рыбы"}

def get_dynamic_ayanamsa(t):
    T = (t.tt - 2451545.0) / 36525.0
    return 23.856235 + (2.30142 * T) + (0.000139 * T**2)

def get_planet_data(t):
    current_ayan = get_dynamic_ayanamsa(t)
    earth = eph['earth']
    planets_objects = {'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 'Mercury': eph['mercury'], 'Jupiter': eph['jupiter_barycenter'], 'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']}
    res = []
    for name, obj in planets_objects.items():
        lon = (earth.at(t).observe(obj).ecliptic_latlon()[1].degrees - current_ayan) % 360
        res.append({'Planet': name, 'Lon': lon, 'Deg': lon % 30})
    
    # Раху (средний узел)
    lat, lon, dist = earth.at(t).observe(eph['moon']).ecliptic_latlon()
    ra_lon = (lon.degrees - current_ayan + 180) % 360 
    res.append({'Planet': 'Rahu', 'Lon': ra_lon, 'Deg': 30 - (ra_lon % 30)}) 
    
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    roles = ['AK', 'AmK', 'BK', 'MK', 'PiK', 'PK', 'GK', 'DK']
    df['Role'] = roles[:len(df)]
    return df, current_ayan

def get_full_info(row):
    nak_idx = int(row['Lon'] / (360/27)) % 27
    sign = ZODIAC_SIGNS[int(row['Lon'] / 30)]
    return f"{P_ICONS.get(row['Planet'], row['Planet'])} в {sign} ({NAKSHATRAS[nak_idx]})"

def create_printable_html(df, title_period):
    """Генерирует HTML-код для идеальной печати на листе А4"""
    rows_html = ""
    for _, row in df.iterrows():
        rows_html += f"""
        <tr>
            <td style="border: 1px solid #ddd; padding: 10px; font-weight: bold; width: 25%;">{row['Время (Сочи)']}</td>
            <td style="border: 1px solid #ddd; padding: 10px; width: 45%;">
                <div style="margin-bottom:4px;"><b>АК:</b> {row['АК']}</div>
                <div><b>AmK:</b> {row['AmK']}</div>
            </td>
            <td style="border: 1px solid #ddd; padding: 10px; color: #eee; vertical-align: bottom;">____________________</td>
        </tr>"""
    
    return f"""
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family: 'Segoe UI', sans-serif; color: #333; padding: 10px;">
        <div style="text-align: center; border-bottom: 2px solid #1B263B; padding-bottom: 10px; margin-bottom: 20px;">
            <h1 style="margin:0; color: #1B263B;">Астрологический План Периодов</h1>
            <p style="margin:5px 0;">Интервал: {title_period} | Часовой пояс: Сочи (UTC+3)</p>
        </div>
        <table style="width: 100%; border-collapse: collapse;">
            <thead>
                <tr style="background: #f8f9fa;">
                    <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Дата и время</th>
                    <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Конфигурация (АК/AmK)</th>
                    <th style="border: 1px solid #ddd; padding: 12px; text-align: left;">Комментарии</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
        <div style="margin-top: 30px; border-top: 1px solid #eee; padding-top: 10px; font-size: 0.8em; text-align: center; color: #888;">
            Сгенерировано Julia Assistant Astro. Для сохранения в PDF нажмите Ctrl+P (Windows) или Cmd+P (Mac).
        </div>
    </body>
    </html>"""

# --- ИНТЕРФЕЙС ---
st.markdown("""
<style>
    .julia-title { text-align: center; font-weight: 800; font-size: 3em; color: #1B263B; margin-bottom: 20px; }
</style>
<h1 class="julia-title">Julia Assistant Astro</h1>
""", unsafe_allow_html=True)

tab1, tab2 = st.tabs(["📊 Прямой эфир", "📅 Высокоточный Таймлайн"])

with tab1:
    st.info("Данные реального времени отображаются здесь. Для планирования перейдите в соседнюю вкладку.")

with tab2:
    st.header("📅 Поиск точных периодов АК/AmK")
    st.write("Выберите любой период с 1940 по 2050 год.")
    
    # Инициализация session_state для сохранения выбора пользователя
    if 's_dt' not in st.session_state: st.session_state.s_dt = datetime.now()
    if 'e_dt' not in st.session_state: st.session_state.e_dt = datetime.now() + timedelta(days=2)

    c1, c2 = st.columns(2)
    with c1:
        # Расширенный диапазон дат
        sd = st.date_input("Дата начала", st.session_state.s_dt.date(), 
                          min_value=datetime(1940, 1, 1), max_value=datetime(2050, 12, 31), key="sd_input")
        st_time = st.time_input("Время начала", st.session_state.s_dt.time(), step=60, key="st_input")
    with c2:
        ed = st.date_input("Дата конца", st.session_state.e_dt.date(), 
                          min_value=datetime(1940, 1, 1), max_value=datetime(2050, 12, 31), key="ed_input")
        et_time = st.time_input("Время конца", st.session_state.e_dt.time(), step=60, key="et_input")

    # Сборка итоговых значений
    dt_start = datetime.combine(sd, st_time)
    dt_end = datetime.combine(ed, et_time)

    if st.button('🚀 Рассчитать и подготовить бланк'):
        if dt_start >= dt_end:
            st.error("Ошибка: Дата начала должна быть раньше даты конца.")
        else:
            with st.spinner('Проводим высокоточный минутный расчет...'):
                curr_utc = dt_start - timedelta(hours=3)
                end_utc = dt_end - timedelta(hours=3)
                events = []
                
                # Начальное состояние
                t_init = ts.utc(curr_utc.year, curr_utc.month, curr_utc.day, curr_utc.hour, curr_utc.minute)
                df_init, _ = get_planet_data(t_init)
                last_pair = f"{df_init.iloc[0]['Planet']}/{df_init.iloc[1]['Planet']}"
                
                events.append({
                    "Время (Сочи)": dt_start.strftime("%d.%m.%Y %H:%M"), 
                    "АК": get_full_info(df_init.iloc[0]), 
                    "AmK": get_full_info(df_init.iloc[1])
                })

                tmp = curr_utc
                # Цикл поиска смен
                while tmp < end_utc:
                    tmp += timedelta(minutes=1)
                    t_s = ts.utc(tmp.year, tmp.month, tmp.day, tmp.hour, tmp.minute)
                    df_s, _ = get_planet_data(t_s)
                    new_p = f"{df_s.iloc[0]['Planet']}/{df_s.iloc[1]['Planet']}"
                    
                    if new_p != last_pair:
                        events.append({
                            "Время (Сочи)": (tmp + timedelta(hours=3)).strftime("%d.%m.%Y %H:%M"), 
                            "АК": get_full_info(df_s.iloc[0]), 
                            "AmK": get_full_info(df_s.iloc[1])
                        })
                        last_pair = new_p
                
                df_res = pd.DataFrame(events)
                st.table(df_res)
                
                # Формирование кнопки ПЕЧАТИ
                title_p = f"{sd.strftime('%d.%m.%Y')} — {ed.strftime('%d.%m.%Y')}"
                html_print = create_printable_html(df_res, title_p)
                b64 = base64.b64encode(html_print.encode('utf-8')).decode()
                
                # Кнопка во всю ширину
                print_button = f'''
                    <a href="data:text/html;base64,{b64}" download="Astro_Plan_{sd}.html" style="text-decoration:none;">
                        <div style="background-color: #1B263B; color: white; padding: 18px; text-align: center; 
                             border-radius: 12px; font-weight: bold; font-size: 1.2em; cursor: pointer; border: 1px solid #415A77;">
                            📄 ОТКРЫТЬ ГОТОВЫЙ БЛАНК ДЛЯ ПЕЧАТИ (A4)
                        </div>
                    </a>
                '''
                st.markdown(print_button, unsafe_allow_html=True)
                st.info("☝️ Нажмите кнопку выше, файл откроется в новой вкладке. Используйте Ctrl+P для печати или сохранения в PDF.")
