import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta
import pandas as pd
import streamlit.components.v1 as components
import math
import os

# 1. Системные настройки
st.set_page_config(page_title="Julia Assistant Astro", layout="wide")

@st.cache_resource
def init_engine():
    ts = load.timescale()
    eph = load('de421.bsp')
    return ts, eph

ts, eph = init_engine()

# --- Константы и Словари ---
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]

# Управители накшатр (в порядке от Ашвини до Ревати)
NAK_LORDS = [
    "Кету", "Венера", "Солнце", "Луна", "Марс", "Раху", "Юпитер", "Сатурн", "Меркурий",
    "Кету", "Венера", "Солнце", "Луна", "Марс", "Раху", "Юпитер", "Сатурн", "Меркурий",
    "Кету", "Венера", "Солнце", "Луна", "Марс", "Раху", "Юпитер", "Сатурн", "Меркурий"
]

P_ICONS = {
    'Sun': '☀️ Sun', 'Moon': '🌙 Moon', 'Mars': '🔴 Mars', 
    'Mercury': '☿️ Merc', 'Jupiter': '🔵 Jup', 'Venus': '♀️ Venus', 
    'Saturn': '🪐 Sat', 'Rahu': '🐲 Rahu', 'Ketu': '🐍 Ketu'
}
Z_ICONS = {
    "Овен": "♈ Овен", "Телец": "♉ Телец", "Близнецы": "♊ Близн", "Рак": "♋ Рак", 
    "Лев": "♌ Лев", "Дева": "♍ Дева", "Весы": "♎ Весы", "Скорпион": "♏ Скорп", 
    "Стрелец": "♐ Стрел", "Козерог": "♑ Козег", "Водолей": "♒ Водол", "Рыбы": "♓ Рыбы"
}

def get_dynamic_ayanamsa(t):
    T = (t.tt - 2451545.0) / 36525.0
    return 23.856235 + (2.30142 * T) + (0.000139 * T**2)

def format_deg_to_min(deg_float):
    d = int(deg_float)
    m = int((deg_float - d) * 60)
    s = round((((deg_float - d) * 60) - m) * 60, 1)
    return f"{d}° {m}' {s}\""

def get_planet_data(t):
    current_ayan = get_dynamic_ayanamsa(t)
    earth = eph['earth']
    planets_objects = {
        'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 
        'Mercury': eph['mercury'], 'Jupiter': eph['jupiter_barycenter'], 
        'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']
    }
    res = []
    for name, obj in planets_objects.items():
        lon = (earth.at(t).observe(obj).ecliptic_latlon()[1].degrees - current_ayan) % 360
        res.append({'Planet': name, 'Lon': lon, 'Deg': lon % 30})
    
    lat, lon, dist = earth.at(t).observe(eph['moon']).ecliptic_latlon()
    ra_lon = (lon.degrees - current_ayan + 180) % 360 
    res.append({'Planet': 'Rahu', 'Lon': ra_lon, 'Deg': 30 - (ra_lon % 30)}) 
    
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    roles = ['AK', 'AmK', 'BK', 'MK', 'PiK', 'PK', 'GK', 'DK']
    df['Role'] = roles[:len(df)]
    
    ketu_lon = (ra_lon + 180) % 360
    ketu_row = pd.DataFrame([{'Planet': 'Ketu', 'Lon': ketu_lon, 'Deg': ketu_lon % 30, 'Role': '-'}])
    df = pd.concat([df, ketu_row], ignore_index=True)
    return df, current_ayan

def get_lunar_info(t):
    earth = eph['earth']
    s_lon = earth.at(t).observe(eph['sun']).ecliptic_latlon()[1].degrees
    m_lon = earth.at(t).observe(eph['moon']).ecliptic_latlon()[1].degrees
    diff = (m_lon - s_lon) % 360
    tithi_num = math.ceil(diff / 12) or 1
    phase_icon = ["🌑","🌒","🌓","🌔","🌕","🌖","🌗","🌘"][int(diff/45) % 8]
    status = "Растущая (Шукла Пакша)" if diff < 180 else "Убывающая (Кришна Пакша)"
    return tithi_num, status, phase_icon

def get_full_info(row):
    nak_idx = int(row['Lon'] / (360/27)) % 27
    sign_name = ZODIAC_SIGNS[int(row['Lon'] / 30)]
    p = row['Planet']
    nak_name = NAKSHATRAS[nak_idx]
    nak_lord = NAK_LORDS[nak_idx]
    return f"{P_ICONS.get(p, p)} | {Z_ICONS.get(sign_name, sign_name)} | ☸️ {nak_name} ({nak_lord})"

# --- ИНТЕРФЕЙС ---

# Добавление ЛОГОТИПА
col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
with col_l2:
    try:
        # Пытаемся загрузить logo.png из корня репозитория
        # Важно: В Streamlit Cloud это должно быть именно "logo.png" (маленькими буквами)
        st.image("logo.png", use_container_width=True)
    except FileNotFoundError:
        st.warning("⚠️ Файл 'logo.png' не найден в репозитории. Пожалуйста, убедитесь, что ваш переименованный файл лежит в корне GitHub.")
    except Exception as e:
        st.error(f"Ошибка при загрузке логотипа: {e}")

# ОБНОВЛЕННЫЙ СТИЛЬ ЗАГОЛОВКА: Динамический переливающийся градиент (Доп 3)
st.markdown("""
<style>
    @keyframes gradient-shine {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .julia-title {
        text-align: center;
        margin-top: -15px;
        margin-bottom: 30px;
        font-weight: bold;
        font-size: 3em;
        /* Переливающийся градиент: Фиолетовый -> Бирюзовый -> Жемчужный */
        background: linear-gradient(270deg, #6A5ACD, #40E0D0, #E0FFFF, #6A5ACD);
        background-size: 800% 800%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradient-shine 15s ease infinite;
    }
</style>
<h1 class="julia-title">Julia Assistant Astro Coordination Center</h1>
""", unsafe_allow_html=True)

# Часы Сочи через HTML/JS
components.html("""
    <div style="background: linear-gradient(90deg, #1a1a2e, #16213e); padding:15px; border-radius:15px; text-align:center; font-family: sans-serif; border: 1px solid #6A5ACD; box-shadow: 0 4px 6px rgba(0,0,0,0.3);">
        <h2 id="clock" style="margin:0; color:#E0E0E0; letter-spacing: 2px; font-weight: bold;">Загрузка...</h2>
        <p style="margin:0; color:#AAA; font-size: 0.9em; text-transform: uppercase; margin-top: 5px;">Sochi Astro-Coordination Time (UTC+3)</p>
    </div>
    <script>
        function updateClock() {
            let d = new Date();
            let utc = d.getTime() + (d.getTimezoneOffset() * 60000);
            let sochi = new Date(utc + (3600000 * 3));
            document.getElementById('clock').innerHTML = sochi.toLocaleTimeString('ru-RU');
        }
        setInterval(updateClock, 1000); updateClock();
    </script>
""", height=115)

tab1, tab2 = st.tabs(["📊 Прямой эфир", "📅 План на неделю"])

with tab1:
    now = datetime.utcnow()
    t_now = ts.utc(now.year, now.month, now.day, now.hour, now.minute, now.second)
    df, ayan_val = get_planet_data(t_now)
    tithi, l_status, l_icon = get_lunar_info(t_now)

    # Виджет Луны
    st.markdown(f"""
    <div style="background: #fdfbff; border-left: 5px solid #6A5ACD; padding: 15px; border-radius: 10px; margin-bottom: 20px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
        <h3 style="margin:0; color: #4B0082;">{l_icon} Статус Луны</h3>
        <p style="font-size: 1.1em; margin: 5px 0;"><b>Титхи (Лун.сутки):</b> {tithi} | <b>Фаза:</b> {l_status}</p>
    </div>
    """, unsafe_allow_html=True)

    # Виджет Айанамши (Доп 1: Служебная информация)
    st.markdown(f"""
        <style>
            .ayan-box {{
                background-color: #f0f8ff; /* AliceBlue */
                border-left: 5px solid #6A5ACD;
                padding: 15px;
                border-radius: 10px;
                margin-bottom: 10px;
            }}
            .ayan-title {{
                color: #4B0082;
                margin-top: 0;
            }}
            .ayan-value {{
                font-size: 1.2em;
                font-weight: bold;
                color: #333;
            }}
            .ayan-service {{
                font-size: 0.9em;
                color: #666;
                margin-top: 5px;
            }}
        </style>
        <div class="ayan-box">
            <h4 class="ayan-title">🔮 Айанамша Лахири (динамическая):</h4>
            <span class="ayan-value">{format_deg_to_min(ayan_val)}</span>
            <div class="ayan-service">Расчет: прецессия от эпохи J2000.0 (стандарт Лахири) с коррекцией на текущую эпоху t.tt</div>
        </div>
    """, unsafe_allow_html=True)
    
    # Основная таблица
    df_v = df.copy()
    df_v['Знак'] = df_v['Lon'].apply(lambda x: Z_ICONS[ZODIAC_SIGNS[int(x/30)]])
    
    def format_nak(lon):
        idx = int(lon / (360/27)) % 27
        return f"{NAKSHATRAS[idx]} ({NAK_LORDS[idx]})"
    
    df_v['Накшатра (Лорд)'] = df_v['Lon'].apply(format_nak)
    df_v['Градус'] = df_v['Deg'].apply(lambda x: f"{x:.4f}°")
    
    # ПРИМЕНЕНИЕ НУМЕРАЦИИ С 1 (Доп 2)
    df_v.index = df_v.index + 1
    
    # Цветовая схема для таблицы (в стиле Венеры в Рыбах)
    st.markdown("""
        <style>
            table.dataframe { border-collapse: collapse; border: 1px solid #6A5ACD; color: #333; width: 100%; }
            table.dataframe thead th { background: linear-gradient(180deg, #f3f0ff, #e0e0ff); border-bottom: 2px solid #6A5ACD; text-align: left; }
            table.dataframe tbody tr:nth-child(even) { background-color: #f8f8ff; }
            table.dataframe td { padding: 8px; border: 1px solid #e0e0e0; }
        </style>
    """, unsafe_allow_html=True)

    # Используем st.dataframe для лучшего форматирования, чем st.table
    st.dataframe(df_v[['Role', 'Planet', 'Знак', 'Накшатра (Лорд)', 'Градус']], use_container_width=True)

    st.markdown("---")
    st.subheader("🔄 Мониторинг ротаций (АК / AmK)")
    
    # ИСПРАВЛЕННАЯ СТРОКА (fix NameError from previous step)
    ak_now, amk_now = df.iloc[0]['Planet'], df.iloc[1]['Planet']
    
    col1, col2 = st.columns(2)

    with col1:
        st.write("⬅️ **Предыдущая смена:**")
        found_prev = False
        # Проверка каждые 10 минут на протяжении 48 часов (2880 минут)
        for m in range(1, 2880, 10):
            past_time = now - timedelta(minutes=m)
            t_p = ts.utc(past_time.year, past_time.month, past_time.day, past_time.hour, past_time.minute)
            df_p, _ = get_planet_data(t_p)
            if df_p.iloc[0]['Planet'] != ak_now or df_p.iloc[1]['Planet'] != amk_now:
                st.warning(f"📅 {(past_time + timedelta(hours=3)).strftime('%d.%m %H:%M')}")
                st.write(f"**АК:** {get_full_info(df_p.iloc[0])}")
                st.write(f"**AmK:** {get_full_info(df_p.iloc[1])}")
                found_prev = True; break
        if not found_prev: st.write("Не найдено")

    with col2:
        st.write("➡️ **Следующая смена:**")
        found_next = False
        for m in range(1, 2880, 10):
            future_time = now + timedelta(minutes=m)
            t_f = ts.utc(future_time.year, future_time.month, future_time.day, future_time.hour, future_time.minute)
            df_f, _ = get_planet_data(t_f)
            if df_f.iloc[0]['Planet'] != ak_now or df_f.iloc[1]['Planet'] != amk_now:
                st.success(f"📅 {(future_time + timedelta(hours=3)).strftime('%d.%m %H:%M')}")
                st.write(f"**АК:** {get_full_info(df_f.iloc[0])}")
                st.write(f"**AmK:** {get_full_info(df_f.iloc[1])}")
                found_next = True; break
        if not found_next: st.write("Не найдено")

    st.markdown("---")
    st.info("💎 **Текущий активный период:**")
    c_ak, c_amk = st.columns(2)
    c_ak.metric("Текущая АК", get_full_info(df.iloc[0]))
    c_amk.metric("Текущая AmK", get_full_info(df.iloc[1]))

with tab2:
    st.header("Таймлайн на неделю")
    @st.cache_data(ttl=3600)
    def generate_plan():
        ref = datetime.utcnow() + timedelta(hours=3)
        start = ref - timedelta(days=ref.weekday()); start = start.replace(hour=0, minute=0)
        events, last_pair = [], ""
        # Проверка каждый час на протяжении недели
        for h in range(0, 168, 1):
            ct = start + timedelta(hours=h)
            t_w = ts.utc(ct.year, ct.month, ct.day, ct.hour-3, 0)
            df_w, _ = get_planet_data(t_w)
            pair = f"{df_w.iloc[0]['Planet']}/{df_w.iloc[1]['Planet']}"
            if pair != last_pair:
                events.append({"Дата/Время": ct.strftime("%d.%m %H:00"), "АК": get_full_info(df_w.iloc[0]), "AmK": get_full_info(df_w.iloc[1])})
                last_pair = pair
        return pd.DataFrame(events)

    if st.button('Сгенерировать план'):
        df_plan = generate_plan()
        # Применение нумерации с 1 для плана
        df_plan.index = df_plan.index + 1
        st.dataframe(df_plan, use_container_width=True)
        components.html("""
        <script>function pr(){window.print();}</script>
        <button onclick='pr()' style='width:100%; height:45px; background:linear-gradient(270deg, #6A5ACD, #40E0D0, #E0FFFF, #6A5ACD); background-size: 800% 800%; animation:gradient-shine 15s ease infinite; color:white; border:none; border-radius:10px; cursor:pointer; font-weight:bold; font-size: 1.1em;'>🖨 ПЕЧАТЬ ПЛАНА</button>
        <style>@keyframes gradient-shine { 0% { background-position: 0% 50%; } 50% { background-position: 100% 50%; } 100% { background-position: 0% 50%; } }</style>
        """, height=60)
