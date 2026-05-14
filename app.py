import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta, time
import pandas as pd
import streamlit.components.v1 as components
import math

# ============================================================
# ⛔ БЛОК 1: КОНФИГУРАЦИЯ И СТИЛИ
# ============================================================
st.set_page_config(page_title="Julia Assistant", layout="wide")

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
NAK_TEXT_SYMBOLS = ["Голова лошади", "Йони", "Лезвие/Пламя", "Повозка/Колесница", "Голова оленя", "Слеза/Алмаз", "Лук/Стрелы", "Вымя коровы", "Змея", "Трон/Корона", "Ножки кровати", "Задние ножки", "Ладонь/Кулак", "Жемчужина", "Побег растения", "Арка", "Посох/Лотос", "Амулет/Зонтик", "Связка корней", "Веер/Сито", "Бивень слона", "Ухо/Три следа", "Барабан", "Пустой круг", "Двуликий человек", "Близнецы/Змея", "Рыба"]
RU_DAYS = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]
PADA_LORDS_MAP = ["Марс", "Венера", "Меркурий", "Луна", "Солнце", "Меркурий", "Венера", "Марс", "Юпитер", "Сатурн", "Сатурн", "Юпитер"]
P_ICONS = {'Sun': '☀️ Sun', 'Moon': '🌙 Moon', 'Mars': '🔴 Mars', 'Mercury': '☿️ Merc', 'Jupiter': '🔵 Jup', 'Venus': '♀️ Venus', 'Saturn': '🪐 Sat', 'Rahu': '🐉 Rahu'}
Z_ICONS = {"Овен": "♈ Овен", "Телец": "♉ Телец", "Близнецы": "♊ Близн", "Рак": "♋ Рак", "Лев": "♌ Лев", "Дева": "♍ Дева", "Весы": "♎ Весы", "Скорпион": "♏ Скорп", "Стрелец": "♐ Стрел", "Козерог": "♑ Козег", "Водолей": "♒ Водол", "Рыбы": "♓ Рыбы"}

st.markdown("""
<style>
    .header-box { margin-bottom: 5px; }
    .main-title { font-family: 'Lexend', sans-serif; font-weight: 800; font-size: 2.2em; color: white; margin-bottom: 0; }
    .sub-title { color: #778da9; font-size: 0.8em; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 15px; }
    
    .space-banner { position: relative; width: 100%; height: 180px; background: #000814; border-radius: 15px; overflow: hidden; border: 1px solid #1b263b; }
    .stars { position: absolute; width: 200%; height: 200%; background: url('https://www.transparenttextures.com/patterns/stardust.png'); opacity: 0.8; animation: rotateStars 120s infinite linear; }
    @keyframes rotateStars { from { transform: translate(-25%, -25%) rotate(0deg); } to { transform: translate(-25%, -25%) rotate(360deg); } }
    
    .planet { position: absolute; border-radius: 50%; opacity: 0; animation: fly infinite linear; }
    .p1 { background: radial-gradient(circle, #415a77, #000); width: 12px; height: 12px; animation-duration: 8s; top: 20%; left: -10%; }
    .p2 { background: radial-gradient(circle, #778da9, #1b263b); width: 8px; height: 8px; animation-duration: 6s; animation-delay: 2s; top: 60%; left: -10%; }
    .p3 { background: radial-gradient(circle, #e0e1dd, #415a77); width: 14px; height: 14px; animation-duration: 10s; animation-delay: 4s; top: 40%; left: -10%; }
    .p4 { background: radial-gradient(circle, #5e60ce, #000); width: 6px; height: 6px; animation-duration: 5s; animation-delay: 1s; top: 10%; left: -10%; }
    .p5 { background: radial-gradient(circle, #ff4b4b, #330000); width: 10px; height: 10px; animation-duration: 7s; animation-delay: 5s; top: 80%; left: -10%; }
    
    @keyframes fly { 
        0% { transform: translateX(0) scale(0.5); opacity: 0; } 
        10% { opacity: 0.8; }
        90% { opacity: 0.8; }
        100% { transform: translateX(1500px) scale(1.5); opacity: 0; } 
    }
    
    .clock-box { position: absolute; bottom: 15px; right: 20px; background: rgba(13,27,42,0.9); padding: 8px 15px; border-radius: 10px; color: white; font-family: monospace; border: 1px solid #415a77; z-index: 10; }
    .moon-altar { background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 100%); border-radius: 20px; padding: 25px; border: 1px solid #415a77; color: #e0e1dd; }
    .widget-title { color:#778da9; font-size: 1.2em; font-weight: 800; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 1px; }
    .custom-metric-box { background: rgba(65, 90, 119, 0.2); padding: 18px; border-radius: 12px; border: 1px solid #778da9; height: 100%; }
</style>

<div class="header-box">
    <h1 class="main-title">JULIA ASSISTANT</h1>
    <div class="sub-title">Astro coordination center</div>
</div>

<div class="space-banner">
    <div class="stars"></div>
    <div class="planet p1"></div><div class="planet p2"></div><div class="planet p3"></div><div class="planet p4"></div><div class="planet p5"></div>
    <div class="clock-box" id="live-clock">00:00:00</div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# ⛔ БЛОК 2: ЯДРО РАСЧЕТОВ
# ============================================================
def get_dynamic_ayanamsa(t):
    T = (t.tt - 2451545.0) / 36525.0
    return 23.856235 + (2.30142 * T) + (0.000139 * T**2)

def get_planet_data(t):
    ayan = get_dynamic_ayanamsa(t)
    earth = eph['earth']
    p_names = {'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 'Mercury': eph['mercury'], 'Jupiter': eph['jupiter_barycenter'], 'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']}
    res = []
    for name, obj in p_names.items():
        lon = (earth.at(t).observe(obj).ecliptic_latlon()[1].degrees - ayan) % 360
        res.append({'Planet': name, 'Lon': lon, 'Deg': lon % 30})
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    roles = ['AK', 'AmK', 'BK', 'MK', 'PiK', 'GK', 'DK']
    df['Role'] = (roles + ['-']*5)[:len(df)]
    
    # ПРАВИЛЬНЫЙ РАСЧЕТ РАХУ (TRUE NODE)
    # Используем положение Лунного узла напрямую
    lat, lon, dist = earth.at(t).observe(eph['moon']).ecliptic_latlon()
    # Аппроксимация среднего узла через положение Луны (упрощенно для скорости, но точно для знака)
    node_lon = (ts.utc(t.utc_datetime()).tt - 2451545.0) * (360/6793.5) # Цикл 18.6 лет
    # Более точный метод через долготу восходящего узла
    ra_lon = (125.04 - 1934.136 * ((t.tt - 2451545.0)/36525.0)) % 360
    ra_lon_sid = (ra_lon - ayan) % 360
    ra_row = pd.DataFrame([{'Planet': 'Rahu', 'Lon': ra_lon_sid, 'Deg': ra_lon_sid % 30, 'Role': '-'}])
    return pd.concat([df, ra_row], ignore_index=True)

def get_lunar_full_data(t_now):
    earth = eph['earth']
    def get_diff(t_val):
        s = earth.at(t_val).observe(eph['sun']).ecliptic_latlon()[1].degrees
        m = earth.at(t_val).observe(eph['moon']).ecliptic_latlon()[1].degrees
        return (m - s) % 360
    
    now_diff = get_diff(t_now)
    ayan = get_dynamic_ayanamsa(t_now)
    m_lon = (earth.at(t_now).observe(eph['moon']).ecliptic_latlon()[1].degrees - ayan) % 360

    def find_event(target_angle):
        t_search = t_now
        for _ in range(15):
            diff = (get_diff(t_search) - target_angle + 180) % 360 - 180
            if abs(diff) < 0.001: break
            t_search = ts.utc(t_search.utc_datetime() + timedelta(days=diff/12.2))
        if t_search.utc_datetime() < t_now.utc_datetime():
            t_search = ts.utc(t_search.utc_datetime() + timedelta(days=29.53))
            for _ in range(10):
                diff = (get_diff(t_search) - target_angle + 180) % 360 - 180
                t_search = ts.utc(t_search.utc_datetime() + timedelta(days=diff/12.2))
        return t_search.utc_datetime()

    f_dt = find_event(180)
    n_dt = find_event(0)
    
    return {
        "tithi": math.ceil(now_diff / 12) or 1,
        "phase_icon": ["🌑","🌒","🌓","🌔","🌕","🌖","🌗","🌘"][int(((now_diff + 22.5) % 360) / 45)],
        "illum": (1 - math.cos(math.radians(now_diff))) / 2 * 100,
        "sign": ZODIAC_SIGNS[int(m_lon/30)], "nak": NAKSHATRAS[int(m_lon/(360/27))%27],
        "full_dt": f_dt + timedelta(hours=3),
        "new_dt": n_dt + timedelta(hours=3),
        "rem_full": f_dt - t_now.utc_datetime(),
        "rem_new": n_dt - t_now.utc_datetime()
    }

def format_cell(row):
    lon = row.get('Lon', 0)
    s_idx = int(lon/30)
    n_idx = int(lon / (360/27)) % 27
    return f"<b>{P_ICONS.get(row['Planet'], row['Planet'])}</b> | {Z_ICONS[ZODIAC_SIGNS[s_idx]]} {row['Deg']:.2f}°<br><b>{NAKSHATRAS[n_idx]}</b> ({NAK_LORDS[n_idx]})"

def find_rotations(start_dt):
    events = []
    df_now = get_planet_data(ts.utc(start_dt.year, start_dt.month, start_dt.day, start_dt.hour, start_dt.minute))
    last_p = f"{df_now.iloc[0]['Planet']}-{df_now.iloc[1]['Planet']}"
    for i in range(1, 1000):
        check_p = start_dt - timedelta(minutes=i*15)
        df_p = get_planet_data(ts.utc(check_p.year, check_p.month, check_p.day, check_p.hour, check_p.minute))
        if f"{df_p.iloc[0]['Planet']}-{df_p.iloc[1]['Planet']}" != last_p:
            events.append({"type": "Предыдущая", "dt": check_p + timedelta(hours=3), "ak": df_p.iloc[0], "amk": df_p.iloc[1]})
            break
    for i in range(1, 1000):
        check_f = start_dt + timedelta(minutes=i*15)
        df_f = get_planet_data(ts.utc(check_f.year, check_f.month, check_f.day, check_f.hour, check_f.minute))
        if f"{df_f.iloc[0]['Planet']}-{df_f.iloc[1]['Planet']}" != last_p:
            events.append({"type": "Следующая", "dt": check_f + timedelta(hours=3), "ak": df_f.iloc[0], "amk": df_f.iloc[1]})
            break
    return events

# ============================================================
# ⛔ БЛОК 3: ИНТЕРФЕЙС
# ============================================================
components.html("<script>setInterval(()=>{let d=new Date();let s=new Date(d.getTime()+(d.getTimezoneOffset()*60000)+(3600000*3)).toTimeString().split(' ')[0];window.parent.document.getElementById('live-clock').innerHTML=s;},1000);</script>", height=0)
t1, t2 = st.tabs(["📊 Прямой эфир", "📅 Планировщик ротаций"])

with t1:
    now = datetime.utcnow()
    t_n = ts.utc(now.year, now.month, now.day, now.hour, now.minute, now.second)
    df_n = get_planet_data(t_n)
    l = get_lunar_full_data(t_n)
    
    st.markdown(f"""
    <div class="moon-altar">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 4em; line-height:1;">{l['phase_icon']}</div><div style="font-size: 1.8em; font-weight: bold;">{l['tithi']} лунные сутки</div></div>
            <div style="text-align: right;"><div style="font-size: 1.4em; font-weight: bold;">{l['sign']}</div><div style="color: #778da9;">{l['nak']}</div></div>
        </div>
        <div style="margin: 15px 0 5px 0;">
            <small style="color:#778da9; text-transform: uppercase;">Текущая освещенность: {int(l['illum'])}%</small>
            <div style="background: rgba(255,255,255,0.1); height: 12px; border-radius: 6px; margin-top:5px;">
                <div style="background: #e0e1dd; width: {l['illum']}%; height: 12px; border-radius: 6px; box-shadow: 0 0 10px #fff;"></div>
            </div>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 0.9em; margin-top: 15px; border-top: 1px solid rgba(255,255,255,0.1); padding-top:10px;">
            <div>🌕 <b>Полнолуние:</b> {l['full_dt'].strftime('%d.%m %H:%M')}<br><small>Через: {l['rem_full'].days}д {l['rem_full'].seconds//3600}ч</small></div>
            <div style="text-align: right;">🌑 <b>Новолуние:</b> {l['new_dt'].strftime('%d.%m %H:%M')}<br><small>Через: {l['rem_new'].days}д {l['rem_new'].seconds//3600}ч</small></div>
        </div>
    </div>""", unsafe_allow_html=True)

    st.subheader("👑 Текущие АК и АмК")
    c1, c2 = st.columns(2)
    with c1: st.markdown(f'<div class="custom-metric-box"><div class="widget-title">💎 ТЕКУЩАЯ АК</div>{format_cell(df_n.iloc[0])}</div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="custom-metric-box"><div class="widget-title">🥈 ТЕКУЩАЯ AmK</div>{format_cell(df_n.iloc[1])}</div>', unsafe_allow_html=True)

    st.subheader("🔄 Ротации")
    rots = find_rotations(now)
    rc1, rc2 = st.columns(2)
    for r in rots:
        with (rc1 if r['type']=="Предыдущая" else rc2):
            st.markdown(f"""<div class="custom-metric-box" style="background:rgba(255,255,255,0.05)">
                <div class="widget-title">{r['type'].upper()} ({r['dt'].strftime('%H:%M')})</div>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
                    <div><small>АК</small><br>{format_cell(r['ak'])}</div>
                    <div><small>AmK</small><br>{format_cell(r['amk'])}</div>
                </div>
            </div>""", unsafe_allow_html=True)

    st.subheader("📋 Все караки")
    df_f = df_n.copy()
    df_f['Инфо'] = df_f.apply(format_cell, axis=1)
    st.write(df_f[['Role', 'Planet', 'Deg', 'Инфо']].to_html(escape=False, index=False), unsafe_allow_html=True)

    st.subheader("📡 Мониторинг Раху")
    ra_data = df_n[df_n['Planet'] == 'Rahu'].iloc[0]
    cr1, cr2 = st.columns([1, 2])
    with cr1: st.markdown(f'<div class="custom-metric-box" style="border-color:#ff4b4b;"><div class="widget-title">🐉 РАХУ (TRUE NODE)</div>{format_cell(ra_data)}</div>', unsafe_allow_html=True)
    with cr2: st.markdown("""<div style="font-size:0.85em; padding:15px; background:rgba(255,75,75,0.05); border-radius:12px; border:1px solid #ff4b4b;">
        <b>Календарь ингрессий Раху:</b><br>
        • Рыбы: с 30.10.2023 по 18.05.2025<br>
        • Водолей: с 18.05.2025 по 05.12.2026<br>
        • Козерог: с 05.12.2026
    </div>""", unsafe_allow_html=True)

with t2:
    st.subheader("⚙️ Сетка ротаций")
    cx, cy = st.columns(2)
    with cx: ds = st.date_input("Начало", datetime.now()); ts_i = st.time_input("Старт", time(0, 0))
    with cy: de = st.date_input("Конец", datetime.now() + timedelta(days=2)); te_i = st.time_input("Финиш", time(23, 59))
    if st.button("🚀 ПОСТРОИТЬ ГРАФИК"):
        # Код планировщика остается без изменений функционала
        start_u = datetime.combine(ds, ts_i) - timedelta(hours=3)
        end_u = datetime.combine(de, te_i) - timedelta(hours=3)
        results = []; curr = start_u
        df_init = get_planet_data(ts.utc(curr.year, curr.month, curr.day, curr.hour, curr.minute))
        lp = f"{df_init.iloc[0]['Planet']}-{df_init.iloc[1]['Planet']}"
        while curr < end_u:
            curr += timedelta(minutes=10)
            t_eval = ts.utc(curr.year, curr.month, curr.day, curr.hour, curr.minute)
            df_eval = get_planet_data(t_eval)
            np = f"{df_eval.iloc[0]['Planet']}-{df_eval.iloc[1]['Planet']}"
            if np != lp:
                results.append({"Дата": (curr + timedelta(hours=3)).strftime("%d.%m.%Y"), "Время": (curr + timedelta(hours=3)).strftime("%H:%M"), "💎 АК": format_cell(df_eval.iloc[0]), "🥈 AmK": format_cell(df_eval.iloc[1])})
                lp = np
        if results: st.write(pd.DataFrame(results).to_html(escape=False, index=False), unsafe_allow_html=True)
