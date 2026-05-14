import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta, time
import pandas as pd
import streamlit.components.v1 as components
import math
import os
import base64

# ============================================================
# ⛔ БЛОК 1: КОНФИГУРАЦИЯ И СТИЛИ
# ============================================================
st.set_page_config(page_title="Julia Assistant Pro", layout="wide")

@st.cache_resource
def init_engine():
    ts = load.timescale()
    try:
        eph = load('de421.bsp')
    except:
        eph = load('de421.bsp') # Повторная попытка если сбой сети
    return ts, eph

ts, eph = init_engine()

# --- СЛОВАРИ ---
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]
NAK_LORDS = ["Кету", "Венера", "Солнце", "Луна", "Марс", "Раху", "Юпитер", "Сатурн", "Меркурий"] * 3
NAK_TEXT_SYMBOLS = ["Голова лошади", "Йони", "Лезвие", "Повозка", "Голова оленя", "Слеза", "Лук", "Вымя коровы", "Змея", "Трон", "Ножки кровати (П)", "Ножки кровати (У)", "Ладонь", "Жемчужина", "Побег", "Арка", "Посох", "Серьга", "Корни", "Веер", "Бивень", "Ухо", "Барабан", "Пустой круг", "Двуликий", "Близнецы", "Рыба"]
RU_DAYS = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]
PADA_LORDS_MAP = ["Марс", "Венера", "Меркурий", "Луна", "Солнце", "Меркурий", "Венера", "Марс", "Юпитер", "Сатурн", "Сатурн", "Юпитер"]
P_ICONS = {'Sun': '☀️ Sun', 'Moon': '🌙 Moon', 'Mars': '🔴 Mars', 'Mercury': '☿️ Merc', 'Jupiter': '🔵 Jup', 'Venus': '♀️ Venus', 'Saturn': '🪐 Sat'}
Z_ICONS = {"Овен": "♈ Овен", "Телец": "♉ Телец", "Близнецы": "♊ Близн", "Рак": "♋ Рак", "Лев": "♌ Лев", "Дева": "♍ Дева", "Весы": "♎ Весы", "Скорпион": "♏ Скорп", "Стрелец": "♐ Стрел", "Козерог": "♑ Козег", "Водолей": "♒ Водол", "Рыбы": "♓ Рыбы"}

# --- СТИЛИ ДЛЯ ПЕЧАТИ И ДИЗАЙНА ---
st.markdown(f"""
<style>
    /* ФИКС ПЕЧАТИ: Заставляем Streamlit показывать всё содержимое */
    @media print {{
        .no-print, [data-testid="stHeader"], [data-testid="stSidebar"], .stTabs [data-baseweb="tab-list"] {{
            display: none !important;
        }}
        .main .block-container {{
            max-width: 100% !important;
            padding: 0 !important;
            margin: 0 !important;
        }}
        /* Убираем скролл-боксы, чтобы печаталось много страниц */
        div[data-testid="stVerticalBlock"] {{
            overflow: visible !important;
            height: auto !important;
        }}
        table {{
            width: 100% !important;
            border-collapse: collapse !important;
            font-size: 10pt !important;
        }}
        th, td {{ border: 1px solid #ddd !important; padding: 8px !important; }}
    }}
    
    .space-banner {{ position: relative; width: 100%; height: 200px; border-radius: 15px; background: black; overflow: hidden; margin-bottom: 20px; }}
    .planet-anim {{ position: absolute; top: 50%; left: 50%; width: 2px; height: 2px; background: white; border-radius: 50%; box-shadow: 0 0 20px 2px white; animation: fly 4s infinite linear; }}
    @keyframes fly {{ 0% {{ transform: scale(0) translate(-50%, -50%); opacity: 1; }} 100% {{ transform: scale(20) translate(-50%, -50%); opacity: 0; }} }}
    .clock-box {{ position: absolute; bottom: 15px; right: 15px; background: rgba(0,0,0,0.6); padding: 10px; border-radius: 8px; color: white; font-family: monospace; }}
    .custom-metric-box {{ background: rgba(65, 90, 119, 0.1); padding: 15px; border-radius: 10px; border: 1px solid rgba(119, 141, 169, 0.2); height: 100%; }}
</style>
<div class="space-banner">
    <div class="planet-anim"></div>
    <div style="position:absolute; top:20px; left:20px; color:white;">
        <h1 style="margin:0;">Julia Assistant</h1>
        <small style="letter-spacing:3px; opacity:0.7;">ASTRO INTELLIGENCE SYSTEM</small>
    </div>
    <div class="clock-box" id="live-clock">00:00:00</div>
</div>
""", unsafe_allow_html=True)

components.html("<script>setInterval(()=>{let d=new Date();let s=new Date(d.getTime()+(d.getTimezoneOffset()*60000)+(3600000*3)).toTimeString().split(' ')[0];window.parent.document.getElementById('live-clock').innerHTML=s;},1000);</script>", height=0)

# ============================================================
# ⛔ БЛОК 2: ЛОГИКА ВЫЧИСЛЕНИЙ
# ============================================================
def get_dynamic_ayanamsa(t):
    T = (t.tt - 2451545.0) / 36525.0
    return 23.856235 + (2.30142 * T) + (0.000139 * T**2)

def get_planet_data(t):
    ayan = get_dynamic_ayanamsa(t)
    earth = eph['earth']
    p_objs = {'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 'Mercury': eph['mercury'], 'Jupiter': eph['jupiter_barycenter'], 'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']}
    res = []
    for name, obj in p_objs.items():
        lon = (earth.at(t).observe(obj).ecliptic_latlon()[1].degrees - ayan) % 360
        res.append({'Planet': name, 'Lon': lon, 'Deg': lon % 30})
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    roles = ['AK', 'AmK', 'BK', 'MK', 'PiK', 'GK', 'DK']
    df['Role'] = roles[:len(df)]
    ra_lon = (earth.at(t).observe(eph['moon']).ecliptic_latlon()[1].degrees - ayan + 180) % 360 
    ra_row = pd.DataFrame([{'Planet': 'Rahu', 'Lon': ra_lon, 'Deg': 30 - (ra_lon % 30), 'Role': '-'}])
    return pd.concat([df, ra_row], ignore_index=True)

def get_lunar_detailed_info(t):
    earth = eph['earth']
    s_pos = earth.at(t).observe(eph['sun']).ecliptic_latlon()
    m_pos = earth.at(t).observe(eph['moon']).ecliptic_latlon()
    diff = (m_pos[1].degrees - s_pos[1].degrees) % 360
    tithi = math.ceil(diff / 12) or 1
    ayan = get_dynamic_ayanamsa(t)
    lon_sid = (m_pos[1].degrees - ayan) % 360
    nak_idx = int(lon_sid / (360/27)) % 27
    sign_idx = int(lon_sid / 30)
    deg_in_sign = lon_sid % 30
    gandanta = ""
    if sign_idx in [3, 7, 11] and deg_in_sign > 27: gandanta = "Реактивная (конец воды)"
    elif sign_idx in [0, 4, 8] and deg_in_sign < 3: gandanta = "Импульсивная (начало огня)"
    
    return {
        "tithi": tithi,
        "phase_icon": ["🌑","🌒","🌓","🌔","🌕","🌖","🌗","🌘"][int(((diff + 22.5) % 360) / 45)],
        "illum": (1 - math.cos(math.radians(diff))) / 2 * 100,
        "to_full": ((180 - diff) % 360) / 0.508,
        "to_new": ((360 - diff) % 360) / 0.508,
        "sign": ZODIAC_SIGNS[sign_idx],
        "nak": NAKSHATRAS[nak_idx],
        "nak_lord": NAK_LORDS[nak_idx],
        "is_waxing": diff < 180,
        "gandanta": gandanta
    }

def get_planner_cell(row):
    lon = row['Lon']
    sign = ZODIAC_SIGNS[int(lon/30)]
    nak_idx = int(lon / (360/27)) % 27
    pada = int((lon % (360/27)) / (360/108)) + 1
    navamsha_sign = int((lon * 9) / 30) % 12
    
    l1 = f"{P_ICONS.get(row['Planet'], row['Planet'])} | {Z_ICONS.get(sign, sign)} {row['Deg']:.2f}°"
    l2 = f"<b>{NAKSHATRAS[nak_idx]}</b> {NAK_LORDS[nak_idx]}"
    l3 = f"{NAK_TEXT_SYMBOLS[nak_idx]}"
    l4 = f"Пада {pada} | Упр: {PADA_LORDS_MAP[navamsha_sign]}"
    return f"{l1}<br>{l2}<br>{l3}<br>{l4}"

# ============================================================
# ⛔ БЛОК 3: ИНТЕРФЕЙС
# ============================================================
tab1, tab2 = st.tabs(["📊 Прямой эфир", "📅 Планировщик ротаций"])

with tab1:
    now_utc = datetime.utcnow()
    t_now = ts.utc(now_utc.year, now_utc.month, now_utc.day, now_utc.hour, now_utc.minute, now_utc.second)
    df = get_planet_data(t_now)
    l = get_lunar_detailed_info(t_now)
    
    # Виджет Луны
    g_html = f'<div style="background:rgba(230,57,70,0.2); border:1px solid #e63946; padding:10px; border-radius:10px; margin-top:10px; color:#ffb3b3;">⚠️ ГАНДАНТА: {l["gandanta"]}</div>' if l['gandanta'] else ''
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #0d1b2a, #1b263b); padding: 20px; border-radius: 15px; border: 1px solid #415a77;">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div><span style="font-size: 3em;">{l['phase_icon']}</span> <b style="font-size: 1.5em;">{l['tithi']} лунный день</b><br>
            <small>{"Растущая" if l['is_waxing'] else "Убывающая"} • {int(l['illum'])}% освещенности</small></div>
            <div style="text-align:right;"><b>{l['sign']}</b><br><small>{l['nak']} (упр. {l['nak_lord']})</small></div>
        </div>
        {g_html}
    </div>""", unsafe_allow_html=True)

    st.subheader("💎 Главные Караки (АК и АмК)")
    c1, c2 = st.columns(2)
    with c1: st.markdown(f'<div class="custom-metric-box"><b>АК (Атма-карака)</b><br>{get_planner_cell(df.iloc[0])}</div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="custom-metric-box"><b>AmK (Аматья-карака)</b><br>{get_planner_cell(df.iloc[1])}</div>', unsafe_allow_html=True)

    st.subheader("📈 Монитор Раху")
    r_deg = df[df['Planet']=='Rahu'].iloc[0]['Deg']
    r_color = "#FF4B4B" if (r_deg < 2 or r_deg > 28) else "#00C853"
    st.markdown(f"<div style='border-left: 5px solid {r_color}; padding-left: 15px;'>Раху в текущем знаке: <b>{r_deg:.2f}°</b></div>", unsafe_allow_html=True)

with tab2:
    st.subheader("⚙️ Настройка расчета")
    col_a, col_b = st.columns(2)
    with col_a:
        d_start = st.date_input("Начало", datetime.now())
        t_start = st.time_input("Время старта", time(0, 0))
    with col_b:
        d_end = st.date_input("Конец", datetime.now() + timedelta(days=2))
        t_end = st.time_input("Время конца", time(23, 59))

    if st.button("🚀 ЗАПУСТИТЬ РАСЧЕТ РОТАЦИЙ"):
        start_dt = datetime.combine(d_start, t_start) - timedelta(hours=3)
        end_dt = datetime.combine(d_end, t_end) - timedelta(hours=3)
        
        # ПРОГРЕСС БАР
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        events = []
        curr = start_dt
        total_seconds = (end_dt - start_dt).total_seconds()
        
        t_init = ts.utc(curr.year, curr.month, curr.day, curr.hour, curr.minute)
        df_init = get_planet_data(t_init)
        last_pair = f"{df_init.iloc[0]['Planet']}-{df_init.iloc[1]['Planet']}"
        
        # Добавляем первую точку
        events.append({
            "Дата": (curr + timedelta(hours=3)).strftime("%d.%m.%Y"),
            "День": RU_DAYS[(curr + timedelta(hours=3)).weekday()],
            "Время": (curr + timedelta(hours=3)).strftime("%H:%M"),
            "💎 АК": get_planner_cell(df_init.iloc[0]),
            "🥈 AmK": get_planner_cell(df_init.iloc[1])
        })

        while curr < end_dt:
            curr += timedelta(minutes=10) # Шаг 10 минут для скорости
            
            # Обновление прогресс-бара
            percent = min(1.0, (curr - start_dt).total_seconds() / total_seconds)
            progress_bar.progress(percent)
            status_text.text(f"Анализ: {(curr + timedelta(hours=3)).strftime('%d.%m %H:%M')}")

            t_loop = ts.utc(curr.year, curr.month, curr.day, curr.hour, curr.minute)
            df_loop = get_planet_data(t_loop)
            new_pair = f"{df_loop.iloc[0]['Planet']}-{df_loop.iloc[1]['Planet']}"
            
            if new_pair != last_pair:
                events.append({
                    "Дата": (curr + timedelta(hours=3)).strftime("%d.%m.%Y"),
                    "День": RU_DAYS[(curr + timedelta(hours=3)).weekday()],
                    "Время": (curr + timedelta(hours=3)).strftime("%H:%M"),
                    "💎 АК": get_planner_cell(df_loop.iloc[0]),
                    "🥈 AmK": get_planner_cell(df_loop.iloc[1])
                })
                last_pair = new_pair
        
        progress_bar.empty()
        status_text.success("✅ Расчет завершен!")

        if events:
            # Кнопка печати
            st.markdown("""
                <button onclick="window.print()" class="no-print" style="
                    width: 100%; padding: 15px; background: #415A77; color: white; 
                    border: none; border-radius: 10px; cursor: pointer; font-weight: bold; margin: 20px 0;
                ">🖨️ РАСПЕЧАТАТЬ ТАБЛИЦУ (CTRL + P)</button>
            """, unsafe_allow_html=True)
            
            # Отображение таблицы
            df_res = pd.DataFrame(events)
            st.write(df_res.to_html(escape=False, index=False), unsafe_allow_html=True)
