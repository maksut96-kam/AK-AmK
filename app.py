import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta, time
import pandas as pd
import os

# ============================================================
# ⛔ БЛОК 1: ФУНДАМЕНТ (НАСТРОЙКИ И ДВИЖОК)
# ============================================================
st.set_page_config(page_title="Julia Assistant Astro Coordination Center", layout="wide")

@st.cache_resource
def init_engine():
    ts = load.timescale()
    eph = load('de421.bsp')
    return ts, eph

ts, eph = init_engine()

# --- СЛОВАРИ И КОНСТАНТЫ ---
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]
NAK_LORDS = ["Кету", "Венера", "Солнце", "Луна", "Марс", "Раху", "Юпитер", "Сатурн", "Меркурий"] * 3

# Чистые иконки без текста
Z_ICONS = {"Овен": "♈", "Телец": "♉", "Близнецы": "♊", "Рак": "♋", "Лев": "♌", "Дева": "♍", "Весы": "♎", "Скорпион": "♏", "Стрелец": "♐", "Козерог": "♑", "Водолей": "♒", "Рыбы": "♓"}

NAK_SYMBOLS_DETAILED = {
    "Ашвини": "Лошадь 🐎", "Бхарани": "Йони ♈", "Криттика": "Бритва 🔪", "Рохини": "Повозка 🛒", 
    "Мригашира": "Олень 🦌", "Аридра": "Слеза 💧", "Пунарвасу": "Лук 🏹", "Пушья": "Вымя 🐄", 
    "Ашлеша": "Змея 🐍", "Магха": "Трон 🏰", "Пурва-пх": "Гамак 🛋️", "Уттара-пх": "Кровать 🛌", 
    "Хаста": "Кисть 🖐️", "Читра": "Алмаз 💎", "Свати": "Росток 🌱", "Вишакха": "Арка ⚖️", 
    "Анурадха": "Цветок 🌸", "Джьештха": "Серьга 🛡️", "Мула": "Корень 🪵", "Пурва-аш": "Бивень 🐘", 
    "Уттара-аш": "Бивень 🐘", "Шравана": "Ухо 👂", "Дхаништха": "Барабан 🥁", "Шатабхиша": "Круг ⚪", 
    "Пурва-бх": "Мечи ⚔️", "Уттара-бх": "Близнецы 👑", "Ревати": "Рыба 🐟"
}

ROLE_RU = {"AK": "АК (Атма-карака)", "AmK": "АмК (Аматья-карака)", "BK": "БК (Бхатри-карака)", "MK": "МК (Матри-карака)", "PiK": "ПиК (Питри-карака)", "GK": "ГК (Гнати-карака)", "DK": "ДК (Дара-карака)"}
P_FULL_NAMES = {'Sun': '☀️ Солнце (Sun)', 'Moon': '🌙 Луна (Moon)', 'Mars': '🔴 Марс (Mars)', 'Mercury': '☿️ Меркурий (Mercury)', 'Jupiter': '🔵 Юпитер (Jupiter)', 'Venus': '♀️ Венера (Venus)', 'Saturn': '🪐 Сатурн (Saturn)'}

# ============================================================
# ⛔ БЛОК 2: АСТРО-ЛОГИКА (ЯДРО)
# ============================================================
def get_dynamic_ayanamsa(t):
    T = (t.tt - 2451545.0) / 36525.0
    return 23.856235 + (2.30142 * T) + (0.000139 * T**2)

def get_planet_data(t):
    ayan = get_dynamic_ayanamsa(t)
    earth = eph['earth']
    planets_objects = {'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 'Mercury': eph['mercury'], 'Jupiter': eph['jupiter_barycenter'], 'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']}
    res = []
    for name, obj in planets_objects.items():
        lon = (earth.at(t).observe(obj).ecliptic_latlon()[1].degrees - ayan) % 360
        res.append({'Planet': name, 'Lon': lon, 'Deg': lon % 30})
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    df['Role'] = ['AK', 'AmK', 'BK', 'MK', 'PiK', 'GK', 'DK'][:len(df)]
    ra_lon = (earth.at(t).observe(eph['moon']).ecliptic_latlon()[1].degrees - ayan + 180) % 360 
    ra_deg = 30 - (ra_lon % 30) 
    return df, ra_lon, ra_deg

def get_extended_info(row):
    sign_idx = int(row['Lon']/30)
    sign_name = ZODIAC_SIGNS[sign_idx]
    nak_idx = int(row['Lon']/(360/27)) % 27
    nak_name = NAKSHATRAS[nak_idx]
    return {
        "role_ru": ROLE_RU.get(row['Role'], row['Role']),
        "planet_full": P_FULL_NAMES.get(row['Planet'], row['Planet']),
        "sign_name": sign_name,
        "sign_icon": Z_ICONS.get(sign_name, ""),
        "degree": f"{row['Deg']:.4f}°",
        "nak_full": f"{nak_name} ({NAK_LORDS[nak_idx]})",
        "nak_sym": NAK_SYMBOLS_DETAILED.get(nak_name, "✨")
    }

def get_xau_storms(dt_start, days=45):
    storms = []
    earth = eph['earth']
    for i in range(days):
        check_date = dt_start + timedelta(days=i)
        t_check = ts.utc(check_date.year, check_date.month, check_date.day)
        ayan = get_dynamic_ayanamsa(t_check)
        sun_lon = (earth.at(t_check).observe(eph['sun']).ecliptic_latlon()[1].degrees - ayan) % 360
        _, ra_lon_check, _ = get_planet_data(t_check)
        diff = abs(sun_lon - ra_lon_check) % 360
        for p in [0, 90, 180, 270]:
            if abs(diff - p) < 3:
                storms.append({"Дата": check_date.strftime("%d.%m"), "Тип": "⚠️ ШТОРМ" if p in [0, 180] else "⚡️ ВОЛАТИЛЬНОСТЬ", "Угол": f"{int(p)}°"})
                break
    seen, unique = set(), []
    for s in storms:
        if s["Дата"] not in seen: unique.append(s); seen.add(s["Дата"])
    return unique[:5]

# ============================================================
# ⛔ БЛОК 3: ИНТЕРФЕЙС (ШАПКА И ЧАСЫ)
# ============================================================
col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
with col_l2:
    if os.path.exists("logo.png"): st.image("logo.png", use_container_width=True)

st.markdown('<h1 style="text-align:center; color:#E2E8F0; margin-bottom:0;">Julia Assistant Astro Coordination Center</h1>', unsafe_allow_html=True)

st.iframe("""
    <div style="background: linear-gradient(90deg, #050510, #0a0a20); padding:10px; border-radius:12px; text-align:center; font-family: sans-serif; border: 1px solid #1B263B;">
        <h2 id="clock" style="margin:0; color:#415A77; letter-spacing: 2px;">Загрузка...</h2>
        <p style="margin:0; color:#778DA9; font-size: 0.8em; text-transform: uppercase;">Sochi Time (UTC+3)</p>
    </div>
    <script>
        function updateClock() { let d = new Date(); let utc = d.getTime() + (d.getTimezoneOffset() * 60000); let sochi = new Date(utc + (3600000 * 3)); document.getElementById('clock').innerHTML = sochi.toLocaleTimeString('ru-RU'); }
        setInterval(updateClock, 1000); updateClock();
    </script>
""", height=100)

# ============================================================
# ⛔ БЛОК 4: МОНИТОРИНГ (TAB 1)
# ============================================================
tab1, tab2 = st.tabs(["📊 Прямой эфир", "📅 Высокоточный Планировщик"])

with tab1:
    now_utc = datetime.utcnow()
    t_now = ts.utc(now_utc.year, now_utc.month, now_utc.day, now_utc.hour, now_utc.minute, now_utc.second)
    df, ra_lon, ra_deg = get_planet_data(t_now)
    
    # Монитор Раху
    st.markdown("### 🐲 Оперативный монитор Раху")
    if ra_deg < 2 or ra_deg > 28: label, color, bg = "КРИТИЧЕСКИЙ ХАОС", "#FF4B4B", "#311717"
    elif ra_deg < 5 or ra_deg > 25: label, color, bg = "ПОВЫШЕННЫЙ РИСК", "#FFA500", "#332616"
    else: label, color, bg = "ТЕХНИЧНЫЙ РЫНОК", "#00C853", "#162B1D"
    
    st.markdown(f"""
    <div style="background:{bg}; border:1px solid {color}; padding:20px; border-radius:12px; color:white;">
        <div style="display:flex; justify-content:space-between;">
            <b style="font-size:1.3em; color:{color};">{label}</b>
            <b style="font-family:monospace; font-size:1.2em;">{ra_deg:.4f}°</b>
        </div>
    </div>""", unsafe_allow_html=True)

    # Карточки АК/АмК
    st.subheader("🔄 Текущая АК и AmK")
    d_ak = get_extended_info(df.iloc[0])
    d_amk = get_extended_info(df.iloc[1])
    
    c1, c2 = st.columns(2)
    for col, d, title in zip([c1, c2], [d_ak, d_amk], ["💎 Атма-карака (АК)", "🥈 Аматья-карака (АмК)"]):
        col.markdown(f"""<div style="background:#0D1B2A; padding:20px; border-radius:10px; border-left: 5px solid #38BDF8; min-height:150px;">
            <small style="color:#778DA9; font-weight:bold;">{title}</small><br>
            <b style="font-size:1.6em; color:white;">{d['planet_full']}</b><br>
            <span style="color:#38BDF8; font-size:1.1em;">{d['sign_icon']} {d['sign_name']} {d['degree']}</span><br>
            <div style="margin-top:8px; color:#F1F5F9;">{d['nak_full']} | {d['nak_sym']}</div>
        </div>""", unsafe_allow_html=True)

    # Таблица чара-карак
    st.markdown("### 📊 ПОЛНЫЙ СПИСОК ЧАРА-КАРАК")
    rows_html = ""
    for _, row in df.iterrows():
        d = get_extended_info(row)
        rows_html += f"""
        <tr style="border-bottom: 1px solid #2D3E50;">
            <td style="padding:14px; color:#94A3B8; font-weight:600; font-size:0.9em;">{d['role_ru']}</td>
            <td style="padding:14px; color:white; font-size:1.1em;">{d['planet_full']}</td>
            <td style="padding:14px; color:#E2E8F0;">{d['sign_icon']} {d['sign_name']}</td>
            <td style="padding:14px; color:#38BDF8; font-family:monospace; font-weight:bold;">{d['degree']}</td>
            <td style="padding:14px; color:#F1F5F9;">{d['nak_full']}</td>
            <td style="padding:14px; color:#CBD5E1; font-style:italic;">{d['nak_sym']}</td>
        </tr>"""
    
    st.markdown(f"""
    <div style="background:#0F172A; border-radius:12px; border:1px solid #1E293B; padding:10px; overflow-x:auto;">
        <table style="width:100%; border-collapse:collapse; text-align:left; font-family:sans-serif;">
            <thead style="background:#1B263B; color:#64748B; font-size:0.85em;">
                <tr>
                    <th style="padding:15px;">РОЛЬ</th><th style="padding:15px;">ПЛАНЕТА</th>
                    <th style="padding:15px;">ЗНАК</th><th style="padding:15px;">ГРАДУС</th>
                    <th style="padding:15px;">НАКШАТРА</th><th style="padding:15px;">СИМВОЛ</th>
                </tr>
            </thead>
            <tbody>{rows_html}</tbody>
        </table>
    </div>""", unsafe_allow_html=True)

# ============================================================
# ⛔ БЛОК 5: ПЛАНИРОВЩИК (TAB 2)
# ============================================================
with tab2:
    st.header("📅 Планировщик ротаций")
    cp1, cp2 = st.columns(2)
    d_start = cp1.date_input("Начало", datetime.now())
    t_start = cp1.time_input("Время ", time(0, 0))
    d_end = cp2.date_input("Конец", datetime.now() + timedelta(days=2))
    t_end = cp2.time_input("Время  ", time(23, 59))

    if st.button('🚀 Сформировать график'):
        curr = datetime.combine(d_start, t_start) - timedelta(hours=3)
        limit = datetime.combine(d_end, t_end) - timedelta(hours=3)
        events = []
        
        # Начальная точка
        t_init = ts.utc(curr.year, curr.month, curr.day, curr.hour, curr.minute)
        df_init, _, _ = get_planet_data(t_init)
        last_pair = f"{df_init.iloc[0]['Planet']}/{df_init.iloc[1]['Planet']}"
        
        while curr < limit:
            t_loop = ts.utc(curr.year, curr.month, curr.day, curr.hour, curr.minute)
            df_loop, _, _ = get_planet_data(t_loop)
            new_pair = f"{df_loop.iloc[0]['Planet']}/{df_loop.iloc[1]['Planet']}"
            
            if new_pair != last_pair or len(events) == 0:
                d1 = get_extended_info(df_loop.iloc[0])
                d2 = get_extended_info(df_loop.iloc[1])
                events.append({
                    "Время (Сочи)": (curr + timedelta(hours=3)).strftime("%d.%m %H:%M"),
                    "💎 АК": f"{d1['planet_full']} ({d1['sign_name']})",
                    "🥈 AmK": f"{d2['planet_full']} ({d2['sign_name']})"
                })
                last_pair = new_pair
            curr += timedelta(minutes=10) # Шаг проверки
            
        st.dataframe(pd.DataFrame(events), use_container_width=True)
