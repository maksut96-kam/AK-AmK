import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta, time
import pandas as pd
import streamlit.components.v1 as components
import math
import os
import base64

# ============================================================
# ⛔ БЛОК 1: ДВИЖОК И НАСТРОЙКИ
# ============================================================
st.set_page_config(page_title="Julia Assistant Pro", layout="wide")

@st.cache_resource
def init_engine():
    ts = load.timescale()
    eph = load('de421.bsp')
    return ts, eph

ts, eph = init_engine()

# --- СЛОВАРИ ---
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]
NAK_LORDS = ["Кету", "Венера", "Солнце", "Луна", "Марс", "Раху", "Юпитер", "Сатурн", "Меркурий"] * 3
NAK_TEXT_SYMBOLS = ["Голова лошади, всадник", "Йони, женские органы", "Лезвие, бритва, пламя", "Повозка, храм, дерево", "Голова оленя, горшок", "Слеза, алмаз", "Лук, колчан стрел", "Вымя коровы, лотос", "Свернувшаяся змея", "Трон, паланкин, корона", "Передние ножки кровати", "Задние ножки кровати", "Ладонь, сжатый кулак", "Жемчужина, камень", "Побег растения, меч", "Триумфальная арка", "Посох, лотос", "Амулет, зонтик, серьга", "Связка корней, стрекало", "Веер, ложе, сито", "Бивень слона, кровать", "Ухо, три следа, трезубец", "Барабан, флейта", "Пустой круг, цветы", "Двуликий человек, меч", "Близнецы, змея", "Рыба, барабан"]
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
    p_objs = {'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 'Mercury': eph['mercury'], 'Jupiter': eph['jupiter_barycenter'], 'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']}
    res = []
    for name, obj in p_objs.items():
        lon = (earth.at(t).observe(obj).ecliptic_latlon()[1].degrees - ayan) % 360
        res.append({'Planet': name, 'Lon': lon, 'Deg': lon % 30})
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    df['Role'] = (['AK', 'AmK', 'BK', 'MK', 'PiK', 'GK', 'DK'] + ['-']*10)[:len(df)]
    ra_lon = (earth.at(t).observe(eph['moon']).ecliptic_latlon()[1].degrees - ayan + 180) % 360 
    ra_row = pd.DataFrame([{'Planet': 'Rahu', 'Lon': ra_lon, 'Deg': 30 - (ra_lon % 30), 'Role': '-'}])
    return pd.concat([df, ra_row], ignore_index=True)

def get_lunar_detailed_info(t):
    earth = eph['earth']
    s_p = earth.at(t).observe(eph['sun']).ecliptic_latlon()[1].degrees
    m_p = earth.at(t).observe(eph['moon']).ecliptic_latlon()[1].degrees
    diff = (m_p - s_p) % 360
    ayan = get_dynamic_ayanamsa(t)
    lon_sid = (m_p - ayan) % 360
    sign_idx = int(lon_sid / 30)
    nak_idx = int(lon_sid / (360/27)) % 27
    deg_sign = lon_sid % 30
    gandanta = ""
    if sign_idx in [3, 7, 11] and deg_sign > 27: gandanta = "Реактивная (конец воды)"
    if sign_idx in [0, 4, 8] and deg_sign < 3: gandanta = "Импульсивная (начало огня)"
    return {
        "tithi": math.ceil(diff / 12) or 1,
        "phase_icon": ["🌑","🌒","🌓","🌔","🌕","🌖","🌗","🌘"][int(((diff + 22.5) % 360) / 45)],
        "illum": (1 - math.cos(math.radians(diff))) / 2 * 100,
        "sign": ZODIAC_SIGNS[sign_idx], "nak": NAKSHATRAS[nak_idx], "nak_lord": NAK_LORDS[nak_idx],
        "is_waxing": diff < 180, "gandanta": gandanta,
        "to_full": ((180 - diff) % 360) / 0.508, "to_new": ((360 - diff) % 360) / 0.508
    }

def get_planner_cell(row):
    lon = row['Lon']
    sign_idx = int(lon/30)
    nak_idx = int(lon / (360/27)) % 27
    pada = int((lon % (360/27)) / (360/108)) + 1
    navamsha_sign = int((lon * 9) / 30) % 12
    
    l1 = f"{P_ICONS.get(row['Planet'], row['Planet'])} | {Z_ICONS.get(ZODIAC_SIGNS[sign_idx], ZODIAC_SIGNS[sign_idx])} {row['Deg']:.2f}°"
    l2 = f"<b>{NAKSHATRAS[nak_idx]}</b> ({NAK_LORDS[nak_idx]})"
    l3 = f"{NAK_TEXT_SYMBOLS[nak_idx]}"
    l4 = f"Пада {pada} | Упр: {PADA_LORDS_MAP[navamsha_sign]}"
    return f"{l1}<br>{l2}<br>{l3}<br>{l4}"

# ============================================================
# ⛔ БЛОК 3: ИНТЕРФЕЙС И СТИЛИ
# ============================================================
st.markdown("""
<style>
    .main-title { font-family: 'Lexend', sans-serif; font-weight: 800; font-size: 2.5em; color: white; margin: 0; }
    .space-banner { background: #0d1b2a; padding: 20px; border-radius: 15px; border: 1px solid #415a77; margin-bottom: 20px; position: relative; overflow: hidden; }
    .planet-anim { position: absolute; width: 100%; height: 100%; top: 0; left: 0; pointer-events: none; }
    .moon-altar { background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 100%); border-radius: 20px; padding: 25px; border: 1px solid #415a77; color: #e0e1dd; }
    .progress-fill { background: linear-gradient(90deg, #415a77, #778da9, #e0e1dd); height: 8px; border-radius: 4px; }
    .custom-metric-box { background: rgba(65, 90, 119, 0.2); padding: 15px; border-radius: 12px; border: 1px solid #778da9; }
</style>
<div class="space-banner">
    <h1 class="main-title">JULIA ASSISTANT</h1>
    <div style="color: #778da9; letter-spacing: 5px; font-size: 0.8em;">ASTRO COORDINATION CENTER</div>
    <div id="live-clock" style="position: absolute; right: 20px; bottom: 15px; color: white; font-family: monospace; font-size: 1.2em;"></div>
</div>
""", unsafe_allow_html=True)

components.html("<script>setInterval(()=>{let d=new Date();let s=new Date(d.getTime()+(d.getTimezoneOffset()*60000)+(3600000*3)).toTimeString().split(' ')[0];window.parent.document.getElementById('live-clock').innerHTML=s;},1000);</script>", height=0)

tab1, tab2 = st.tabs(["📊 Прямой эфир", "📅 Планировщик ротаций"])

# --- ВКЛАДКА 1 (ВОЗВРАТ К ОРИГИНАЛУ) ---
with tab1:
    now_utc = datetime.utcnow()
    t_n = ts.utc(now_utc.year, now_utc.month, now_utc.day, now_utc.hour, now_utc.minute, now_utc.second)
    df_n = get_planet_data(t_n)
    l = get_lunar_detailed_info(t_n)
    
    g_alert = f'<div style="background:rgba(230,57,70,0.2); border:1px solid #e63946; padding:10px; border-radius:10px; margin-top:15px; color:#ffb3b3;">⚠️ ГАНДАНТА: {l["gandanta"]}</div>' if l['gandanta'] else ''
    
    st.markdown(f"""
    <div class="moon-altar">
        <div style="display: flex; justify-content: space-between;">
            <div><div style="font-size: 3.5em;">{l['phase_icon']}</div><div style="font-size: 1.8em; font-weight: 700;">{l['tithi']} лунные сутки</div>
            <div style="color: #778da9;">{"Растущая" if l['is_waxing'] else "Убывающая"} • {int(l['illum'])}% света</div></div>
            <div style="text-align: right;"><div style="font-size: 1.2em; font-weight: bold;">{l['sign']}</div><div style="color: #778da9;">{l['nak']} (Лорд: {l['nak_lord']})</div></div>
        </div>
        <div style="background: rgba(255,255,255,0.1); height: 8px; border-radius: 4px; margin: 15px 0;"><div class="progress-fill" style="width: {l['illum']}%"></div></div>
        <div style="display: flex; justify-content: space-between; font-size: 0.85em;"><span>🌕 Полнолуние: {int(l['to_full']//24)}д {int(l['to_full']%24)}ч</span><span>🌑 Новолуние: {int(l['to_new']//24)}д {int(l['to_new']%24)}ч</span></div>
        {g_alert}
        <div style="margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 10px;">💎 <b>Совет:</b> {"Время трансляции идей." if l['is_waxing'] else "Время завершения стратегий."}</div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("👑 Главные Караки")
    ck1, ck2 = st.columns(2)
    with ck1: st.markdown(f'<div class="custom-metric-box"><div style="color:#778da9; font-weight:bold; border-bottom:1px solid rgba(255,255,255,0.1); margin-bottom:10px;">💎 АК (Атма-карака)</div>{get_planner_cell(df_n.iloc[0])}</div>', unsafe_allow_html=True)
    with ck2: st.markdown(f'<div class="custom-metric-box"><div style="color:#778da9; font-weight:bold; border-bottom:1px solid rgba(255,255,255,0.1); margin-bottom:10px;">🥈 AmK (Аматья-карака)</div>{get_planner_cell(df_n.iloc[1])}</div>', unsafe_allow_html=True)

    st.subheader("🐲 Монитор Раху")
    r_deg = df_n[df_n['Planet']=='Rahu'].iloc[0]['Deg']
    r_color = "#FF4B4B" if (r_deg < 2 or r_deg > 28) else "#00C853"
    st.markdown(f"<div style='border-left: 5px solid {r_color}; padding: 15px; background: {r_color}11;'>Раху в текущем знаке: <b>{r_deg:.2f}°</b></div>", unsafe_allow_html=True)

# --- ВКЛАДКА 2 (ПЛАНИРОВЩИК) ---
with tab2:
    st.subheader("⚙️ Настройка расчета")
    c_p1, c_p2 = st.columns(2)
    with c_p1:
        d_s = st.date_input("Начало", datetime.now(), key="ds")
        t_s = st.time_input("Время", time(0, 0), key="ts")
    with c_p2:
        d_e = st.date_input("Конец", datetime.now() + timedelta(days=2), key="de")
        t_e = st.time_input("Время ", time(23, 59), key="te")

    if st.button("🚀 РАССЧИТАТЬ ГРАФИК РОТАЦИЙ"):
        start_utc = datetime.combine(d_s, t_s) - timedelta(hours=3)
        end_utc = datetime.combine(d_e, t_e) - timedelta(hours=3)
        
        prog = st.progress(0)
        stat = st.empty()
        events = []
        
        curr = start_utc
        t_tot = (end_utc - start_utc).total_seconds()
        
        df_init = get_planet_data(ts.utc(curr.year, curr.month, curr.day, curr.hour, curr.minute))
        last_pair = f"{df_init.iloc[0]['Planet']}-{df_init.iloc[1]['Planet']}"
        
        # Первая строка
        events.append({"Дата": (curr + timedelta(hours=3)).strftime("%d.%m.%Y"), "День": RU_DAYS[(curr + timedelta(hours=3)).weekday()], "Время": (curr + timedelta(hours=3)).strftime("%H:%M"), "💎 АК": get_planner_cell(df_init.iloc[0]), "🥈 AmK": get_planner_cell(df_init.iloc[1])})

        while curr < end_utc:
            curr += timedelta(minutes=5)
            p_val = min(1.0, (curr - start_utc).total_seconds() / t_tot)
            prog.progress(p_val)
            stat.text(f"Анализ: {(curr + timedelta(hours=3)).strftime('%d.%m %H:%M')}")
            
            t_loop = ts.utc(curr.year, curr.month, curr.day, curr.hour, curr.minute)
            df_loop = get_planet_data(t_loop)
            new_pair = f"{df_loop.iloc[0]['Planet']}-{df_loop.iloc[1]['Planet']}"
            
            if new_pair != last_pair:
                events.append({"Дата": (curr + timedelta(hours=3)).strftime("%d.%m.%Y"), "День": RU_DAYS[(curr + timedelta(hours=3)).weekday()], "Время": (curr + timedelta(hours=3)).strftime("%H:%M"), "💎 АК": get_planner_cell(df_loop.iloc[0]), "🥈 AmK": get_planner_cell(df_loop.iloc[1])})
                last_pair = new_pair
        
        prog.empty()
        stat.success("Расчет завершен!")
        
        if events:
            df_res = pd.DataFrame(events)
            html_table = df_res.to_html(escape=False, index=False)
            
            # Генерация кода для нового окна
            print_html = f"""
            <html><head><title>Печать ротаций</title><style>
            body {{ font-family: sans-serif; padding: 20px; }}
            table {{ border-collapse: collapse; width: 100%; }}
            th, td {{ border: 1px solid #ccc; padding: 10px; text-align: left; font-size: 12px; }}
            th {{ background: #f2f2f2; }}
            b {{ color: #0d1b2a; }}
            </style></head><body>
            <h2>График ротаций АК/AmK</h2>
            {html_table}
            <script>window.print();</script>
            </body></html>
            """
            b64 = base64.b64encode(print_html.encode()).decode()
            
            st.markdown(f"""
                <a href="data:text/html;base64,{b64}" target="_blank" style="text-decoration:none;">
                    <button style="width:100%; padding:15px; background:#00C853; color:white; border:none; border-radius:10px; cursor:pointer; font-weight:bold; font-size:1.1em;">
                        🖨️ ОТКРЫТЬ ТАБЛИЦУ В НОВОМ ОКНЕ ДЛЯ ПЕЧАТИ
                    </button>
                </a>
            """, unsafe_allow_html=True)
            
            st.write(df_res.to_html(escape=False, index=False), unsafe_allow_html=True)
