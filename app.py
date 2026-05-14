import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta, time
import pandas as pd
import streamlit.components.v1 as components
import math
import os
import base64

# ============================================================
# ⛔ БЛОК 1: ФУНДАМЕНТ
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

NAK_TEXT_SYMBOLS = [
    "Голова лошади, всадник, карета", "Йони, женские органы, лодка", "Лезвие, бритва, нож, пламя", 
    "Повозка, колесница, храм, дерево", "Голова оленя, горшок с сомой", "Слеза, алмаз, человеческая голова", 
    "Лук, колчан стрел, дом", "Вымя коровы, цветок лотоса, круг", "Свернувшаяся змея, колесо", 
    "Трон, паланкин, корона", "Передние ножки кровати, гамак, смоковница", "Задние ножки кровати, гамак, посох", 
    "Ладонь, сжатый кулак, гончарный круг", "Сверкающая жемчужина, драгоценный камень", "Побег растения, коралл, меч", 
    "Триумфальная арка, гончарный круг, ветви", "Посох, лотос, триумфальная арка", "Круглый амулет, зонтик, серьга", 
    "Связка корней, стрекало для слона", "Веер, ложе, сито для веяния зерна", "Бивень слона, маленькая кровать", 
    "Ухо, три следа, трезубец", "Барабан, флейта, корона", "Пустой круг, тысяча цветов", 
    "Передние ножки погребального ложа, двуликий человек, меч", "Задние ножки погребального ложа, близнецы, змея", "Рыба, барабан"
]

RU_DAYS = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]
PADA_LORDS_MAP = ["Марс", "Венера", "Меркурий", "Луна", "Солнце", "Меркурий", "Венера", "Марс", "Юпитер", "Сатурн", "Сатурн", "Юпитер"]

P_ICONS = {'Sun': '☀️ Sun', 'Moon': '🌙 Moon', 'Mars': '🔴 Mars', 'Mercury': '☿️ Merc', 'Jupiter': '🔵 Jup', 'Venus': '♀️ Venus', 'Saturn': '🪐 Sat'}
Z_ICONS = {"Овен": "♈ Овен", "Телец": "♉ Телец", "Близнецы": "♊ Близн", "Рак": "♋ Рак", "Лев": "♌ Лев", "Дева": "♍ Дева", "Весы": "♎ Весы", "Скорпион": "♏ Скорп", "Стрелец": "♐ Стрел", "Козерог": "♑ Козег", "Водолей": "♒ Водол", "Рыбы": "♓ Рыбы"}

# ============================================================
# ⛔ БЛОК 2: МАТЕМАТИКА
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
    df['Role'] = (['AK', 'AmK', 'BK', 'MK', 'PiK', 'GK', 'DK'] + ['-'] * 10)[:len(df)]
    ra_lon = (earth.at(t).observe(eph['moon']).ecliptic_latlon()[1].degrees - ayan + 180) % 360 
    ra_row = pd.DataFrame([{'Planet': 'Rahu', 'Lon': ra_lon, 'Deg': 30 - (ra_lon % 30), 'Role': '-'}])
    df = pd.concat([df, ra_row], ignore_index=True)
    return df, ayan

def get_lunar_detailed_info(t):
    earth = eph['earth']
    s_pos = earth.at(t).observe(eph['sun']).ecliptic_latlon()
    m_pos = earth.at(t).observe(eph['moon']).ecliptic_latlon()
    diff = (m_pos[1].degrees - s_pos[1].degrees) % 360
    tithi_num = math.ceil(diff / 12) or 1
    illumination = (1 - math.cos(math.radians(diff))) / 2 * 100
    ayan = get_dynamic_ayanamsa(t)
    lon_sid = (m_pos[1].degrees - ayan) % 360
    sign_idx = int(lon_sid / 30)
    nak_idx = int(lon_sid / (360/27)) % 27
    gandanta = False
    deg_in_sign = lon_sid % 30
    if sign_idx in [3, 7, 11] and deg_in_sign > 27: gandanta = "Реактивная (конец воды)"
    if sign_idx in [0, 4, 8] and deg_in_sign < 3: gandanta = "Импульсивная (начало огня)"
    return {
        "tithi": tithi_num,
        "phase_icon": ["🌑","🌒","🌓","🌔","🌕","🌖","🌗","🌘"][int(((diff + 22.5) % 360) / 45)],
        "illum": illumination,
        "to_full": ((180 - diff) % 360) / 0.508,
        "to_new": ((360 - diff) % 360) / 0.508,
        "sign": ZODIAC_SIGNS[sign_idx],
        "nak": NAKSHATRAS[nak_idx],
        "nak_lord": NAK_LORDS[nak_idx],
        "is_waxing": diff < 180,
        "gandanta": gandanta
    }

# ИСПРАВЛЕНИЕ 1: Построчный формат для планировщика (HTML)
def get_planner_cell(row):
    lon = row['Lon']
    sign = ZODIAC_SIGNS[int(lon/30)]
    nak_idx = int(lon / (360/27)) % 27
    pada = int((lon % (360/27)) / (360/108)) + 1
    nak = NAKSHATRAS[nak_idx]
    nak_sym = NAK_TEXT_SYMBOLS[nak_idx]
    nak_lord = NAK_LORDS[nak_idx]
    navamsha_sign = int((lon * 9) / 30) % 12
    pada_lord = PADA_LORDS_MAP[navamsha_sign]
    
    line1 = f"{P_ICONS.get(row['Planet'], row['Planet'])} | {Z_ICONS.get(sign, sign)} {row['Deg']:.2f}°"
    line2 = f"<b>{nak}</b> {nak_lord}"
    line3 = f"{nak_sym}"
    line4 = f"Пада {pada} | Упр: {pada_lord}"
    return f"{line1}<br>{line2}<br>{line3}<br>{line4}"

def get_full_info(row):
    return get_planner_cell(row)

# ============================================================
# ⛔ БЛОК 3: ИНТЕРФЕЙС
# ============================================================
def get_base64_img(path):
    if os.path.exists(path):
        with open(path, "rb") as f: return base64.b64encode(f.read()).decode()
    return ""

logo_data = get_base64_img("logo.png")

# ИСПРАВЛЕНИЕ 2: Стилизация для печати (@media print)
st.markdown(f"""
<style>
    @media print {{
        .no-print, .header-wrapper, .space-banner, .stTabs [data-baseweb="tab-list"], 
        .stButton, footer, header, [data-testid="stSidebar"] {{
            display: none !important;
        }}
        .stMain {{ padding: 0 !important; }}
        table {{ font-size: 10pt !important; }}
    }}
    .header-wrapper {{ display: flex; align-items: center; margin-bottom: 20px; }}
    .fish-logo {{ width: 60px; height: 60px; background-image: url('data:image/png;base64,{logo_data}'); background-size: contain; background-repeat: no-repeat; margin-right: 20px; }}
    .main-title {{ font-family: 'Lexend', sans-serif; font-weight: 800; font-size: 2.8em; text-transform: uppercase; color: white; margin: 0; }}
    .space-banner {{ position: relative; width: 100%; height: 300px; border-radius: 20px; overflow: hidden; background: black; border: 1px solid rgba(255,255,255,0.1); }}
    .planet {{ position: absolute; top: 0; left: 0; right: 0; bottom: 0; transform: scale(0); opacity: 0; animation: fly 3s infinite linear; }}
    .p1 {{ background-image: radial-gradient(circle, #415A77 8px, transparent 15px); background-size: 400px 400px; animation-duration: 4s; }}
    .p2 {{ background-image: radial-gradient(circle, #778DA9 4px, transparent 10px); background-size: 300px 300px; animation-duration: 2.5s; animation-delay: 1s; }}
    @keyframes fly {{ 0% {{ transform: scale(0.1); opacity: 0; }} 50% {{ opacity: 1; }} 100% {{ transform: scale(2.5); opacity: 0; }} }}
    .clock-box {{ position: absolute; bottom: 20px; right: 20px; background: rgba(13, 27, 42, 0.7); backdrop-filter: blur(10px); padding: 10px 20px; border-radius: 12px; border: 1px solid rgba(255,255,255,0.1); z-index: 99; }}
    .custom-metric-box {{ background: rgba(65, 90, 119, 0.2); padding: 20px; border-radius: 12px; border: 1px solid rgba(119, 141, 169, 0.3); height: 100%; }}
    .custom-metric-title {{ color: #778DA9; font-size: 1.1em; font-weight: bold; margin-bottom: 10px; border-bottom: 1px solid rgba(119, 141, 169, 0.2); padding-bottom: 5px; }}
    .custom-metric-value {{ font-size: 1.15em; color: white; line-height: 1.5; }}
</style>
<div class="header-wrapper"><div class="fish-logo"></div><div><h1 class="main-title">Julia's Assistant</h1><div style="color: #778DA9; letter-spacing: 5px; font-size: 0.9em;">ASTRO COORDINATION CENTER</div></div></div>
<div class="space-banner"><div class="planet p1"></div><div class="planet p2"></div><div class="clock-box"><span id="live-clock" style="color: white; font-weight: bold; font-family: monospace; font-size: 1.5em;">00:00:00</span><div style="color: #778DA9; font-size: 0.7em; text-transform: uppercase;">Sochi Time</div></div></div>
""", unsafe_allow_html=True)

components.html("<script>function tick() { let d = new Date(); let utc = d.getTime() + (d.getTimezoneOffset() * 60000); let sochi = new Date(utc + (3600000 * 3)); let s = sochi.toTimeString().split(' ')[0]; const el = window.parent.document.getElementById('live-clock'); if (el) el.innerHTML = s; } setInterval(tick, 1000); tick(); </script>", height=0)

# ============================================================
# ⛔ БЛОК 4: МОНИТОРИНГ
# ============================================================
tab1, tab2 = st.tabs(["📊 Прямой эфир", "📅 Высокоточный Планировщик"])

with tab1:
    now_utc = datetime.utcnow()
    t_now = ts.utc(now_utc.year, now_utc.month, now_utc.day, now_utc.hour, now_utc.minute, now_utc.second)
    df, _ = get_planet_data(t_now)
    l = get_lunar_detailed_info(t_now) 
    
    def fmt_h(h): return f"{int(h // 24)}д {int(h % 24)}ч"
    advice = "Время транслировать идеи и расширять контакты." if l['is_waxing'] else "Время анализа и завершения текущих стратегий."
    gandanta_html = f'<div class="gandanta-alert">⚠️ ГАНДАНТА: {l["gandanta"]}</div>' if l['gandanta'] else ''

    st.markdown(f"""<style>
    .moon-altar {{ background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 100%); border-radius: 20px; padding: 25px; border: 1px solid rgba(119, 141, 169, 0.3); color: #e0e1dd; margin-bottom: 25px; }}
    .moon-title {{ font-size: 1.8em; font-weight: 700; margin-bottom: 5px; }}
    .progress-fill {{ background: linear-gradient(90deg, #415a77, #778da9, #e0e1dd); width: {l['illum']}%; height: 8px; border-radius: 4px; box-shadow: 0 0 15px rgba(224, 225, 221, 0.5); }}
    .gandanta-alert {{ background: rgba(230, 57, 70, 0.2); border: 1px solid #e63946; padding: 10px; border-radius: 10px; margin-top: 15px; color: #ffb3b3; text-align: center; }}
    </style>
    <div class="moon-altar">
        <div style="display: flex; justify-content: space-between;">
            <div><div style="font-size: 3.5em;">{l['phase_icon']}</div><div class="moon-title">{l['tithi']} лунные сутки</div>
            <div style="color: #778da9;">{"Растущая" if l['is_waxing'] else "Убывающая"} • {int(l['illum'])}% света</div></div>
            <div style="text-align: right;"><div style="font-size: 1.2em; font-weight: bold;">{l['sign']}</div><div style="color: #778da9;">{l['nak']} (Лорд: {l['nak_lord']})</div></div>
        </div>
        <div style="background: rgba(255,255,255,0.1); height: 8px; border-radius: 4px; margin: 15px 0;"><div class="progress-fill"></div></div>
        <div style="display: flex; justify-content: space-between; font-size: 0.85em;"><span>🌕 Полнолуние: {fmt_h(l['to_full'])}</span><span>🌑 Новолуние: {fmt_h(l['to_new'])}</span></div>
        {gandanta_html}<div style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 10px;">💎 <b>Совет:</b> {advice}</div>
    </div>""", unsafe_allow_html=True)

    st.subheader("☀️ Текущее положение Светил")
    c_s1, c_s2 = st.columns(2)
    with c_s1: st.markdown(f'<div class="custom-metric-box"><div class="custom-metric-title">Солнце</div><div class="custom-metric-value">{get_full_info(df[df["Planet"]=="Sun"].iloc[0])}</div></div>', unsafe_allow_html=True)
    with c_s2: st.markdown(f'<div class="custom-metric-box"><div class="custom-metric-title">Луна</div><div class="custom-metric-value">{get_full_info(df[df["Planet"]=="Moon"].iloc[0])}</div></div>', unsafe_allow_html=True)

    st.subheader("📈 Динамика силы Луны (30 дней)")
    chart_data = [{"Дата": (now_utc + timedelta(days=i)).strftime("%d.%m"), "Свет %": get_lunar_detailed_info(ts.utc((now_utc + timedelta(days=i)).year, (now_utc + timedelta(days=i)).month, (now_utc + timedelta(days=i)).day))['illum']} for i in range(30)]
    st.area_chart(pd.DataFrame(chart_data).set_index("Дата"))

    st.divider()
    st.subheader("👑 Главные Караки")
    ck1, ck2 = st.columns(2)
    with ck1: st.markdown(f'<div class="custom-metric-box"><div class="custom-metric-title">💎 АК (Атма-карака)</div><div class="custom-metric-value">{get_full_info(df.iloc[0])}</div></div>', unsafe_allow_html=True)
    with ck2: st.markdown(f'<div class="custom-metric-box"><div class="custom-metric-title">🥈 AmK (Аматья-карака)</div><div class="custom-metric-value">{get_full_info(df.iloc[1])}</div></div>', unsafe_allow_html=True)

    st.subheader("📊 Таблица Чара-карак")
    df_v = df.copy()
    df_v['Знак'] = df_v['Lon'].apply(lambda x: Z_ICONS[ZODIAC_SIGNS[int(x/30)]])
    df_v['Накшатра'] = df_v.apply(lambda row: f"{NAKSHATRAS[int(row['Lon']/(360/27))%27]}", axis=1)
    df_v['Градус'] = df_v['Deg'].apply(lambda x: f"{x:.4f}°")
    st.dataframe(df_v[['Role', 'Planet', 'Знак', 'Накшатра', 'Градус']], use_container_width=True, hide_index=True)

    ra_row = df[df['Planet'] == 'Rahu'].iloc[0]
    ra_deg = ra_row['Deg']
    if ra_deg < 2 or ra_deg > 28: label, color, desc = "🔴 КРИТИЧЕСКИЙ ХАОС", "#FF4B4B", "Зона Ганданты."
    elif ra_deg < 5 or ra_deg > 25: label, color, desc = "🟡 ПОВЫШЕННЫЙ РИСК", "#FFA500", "Эмоциональные качели."
    else: label, color, desc = "🟢 ТЕХНИЧНЫЙ РЫНОК", "#00C853", "Чистая зона."
    st.markdown(f'<div style="background:{color}22; border-left:5px solid {color}; padding:15px; border-radius:10px; margin-top:20px;"><h3 style="margin:0; color:{color};">🐲 Монитор Раху: {label}</h3><p>{desc} (Градус: {ra_deg:.2f}°)</p></div>', unsafe_allow_html=True)

# ============================================================
# ⛔ БЛОК 5: ПЛАНИРОВЩИК
# ============================================================
with tab2:
    st.header("📅 Высокоточный планировщик")
    c_p1, c_p2 = st.columns(2)
    with c_p1:
        d_s = st.date_input("Дата начала", datetime.now(), key="ds_p")
        t_s = st.time_input("Время начала", time(0, 0), key="ts_p")
    with c_p2:
        d_e = st.date_input("Дата конца", datetime.now() + timedelta(days=2), key="de_p")
        t_e = st.time_input("Время конца", time(23, 59), key="te_p")

    if st.button('🚀 Рассчитать таблицу ротаций'):
        curr_utc = datetime.combine(d_s, t_s) - timedelta(hours=3)
        end_utc = datetime.combine(d_e, t_e) - timedelta(hours=3)
        events = []
        
        t_init = ts.utc(curr_utc.year, curr_utc.month, curr_utc.day, curr_utc.hour, curr_utc.minute)
        df_i, _ = get_planet_data(t_init)
        last_pair = f"{df_i.iloc[0]['Planet']}/{df_i.iloc[1]['Planet']}"
        
        # Первая строка
        s_time = curr_utc + timedelta(hours=3)
        events.append({"Дата": s_time.strftime("%d.%m.%Y"), "День": RU_DAYS[s_time.weekday()], "Время": s_time.strftime("%H:%M"), "💎 АК": get_planner_cell(df_i.iloc[0]), "🥈 AmK": get_planner_cell(df_i.iloc[1])})

        while curr_utc < end_utc:
            curr_utc += timedelta(minutes=5)
            t_loop = ts.utc(curr_utc.year, curr_utc.month, curr_utc.day, curr_utc.hour, curr_utc.minute)
            df_loop, _ = get_planet_data(t_loop)
            new_pair = f"{df_loop.iloc[0]['Planet']}/{df_loop.iloc[1]['Planet']}"
            if new_pair != last_pair:
                s_time = curr_utc + timedelta(hours=3)
                events.append({"Дата": s_time.strftime("%d.%m.%Y"), "День": RU_DAYS[s_time.weekday()], "Время": s_time.strftime("%H:%M"), "💎 АК": get_planner_cell(df_loop.iloc[0]), "🥈 AmK": get_planner_cell(df_loop.iloc[1])})
                last_pair = new_pair
        
        if events:
            df_ev = pd.DataFrame(events)
            
            # Кнопка печати: она просто вызывает окно печати браузера
            st.markdown('<button onclick="window.print()" class="no-print" style="width:100%; padding:15px; background:#415A77; color:white; border:none; border-radius:10px; cursor:pointer; font-weight:bold; margin-bottom:20px;">🖨️ ПОДГОТОВИТЬ ВЕРСИЮ ДЛЯ ПЕЧАТИ</button>', unsafe_allow_html=True)
            
            # Рендерим таблицу как HTML, чтобы работали переносы строк <br> и жирный шрифт
            st.write(df_ev.to_html(escape=False, index=False), unsafe_allow_html=True)
