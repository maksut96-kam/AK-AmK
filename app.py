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

# --- СЛОВАРИ (ПОЛНЫЙ НАБОР) ---
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]
NAK_LORDS = ["Кету", "Венера", "Солнце", "Луна", "Марс", "Раху", "Юпитер", "Сатурн", "Меркурий"] * 3
NAK_TEXT_SYMBOLS = ["Голова лошади", "Йони", "Лезвие/Пламя", "Повозка/Колесница", "Голова оленя", "Слеза/Алмаз", "Лук/Стрелы", "Вымя коровы", "Змея", "Трон/Корона", "Ножки кровати", "Задние ножки", "Ладонь/Кулак", "Жемчужина", "Побег растения", "Арка", "Посох/Лотос", "Амулет/Зонтик", "Связка корней", "Веер/Сито", "Бивень слона", "Ухо/Три следа", "Барабан", "Пустой круг", "Двуликий человек", "Близнецы/Змея", "Рыба"]
PADA_LORDS_MAP = ["Марс", "Венера", "Меркурий", "Луна", "Солнце", "Меркурий", "Венера", "Марс", "Юпитер", "Сатурн", "Сатурн", "Юпитер"]
P_ICONS = {'Sun': '☀️ Sun', 'Moon': '🌙 Moon', 'Mars': '🔴 Mars', 'Mercury': '☿️ Merc', 'Jupiter': '🔵 Jup', 'Venus': '♀️ Venus', 'Saturn': '🪐 Sat', 'Rahu': '🐉 Rahu'}
Z_ICONS = {"Овен": "♈ Овен", "Телец": "♉ Телец", "Близнецы": "♊ Близн", "Рак": "♋ Рак", "Лев": "♌ Лев", "Дева": "♍ Дева", "Весы": "♎ Весы", "Скорпион": "♏ Скорп", "Стрелец": "♐ Стрел", "Козерог": "♑ Козег", "Водолей": "♒ Водол", "Рыбы": "♓ Рыбы"}

st.markdown("""
<style>
    .header-box { margin-bottom: 5px; }
    .main-title { font-family: 'Lexend', sans-serif; font-weight: 800; font-size: 2.2em; color: white; margin: 0; }
    .sub-title { color: #778da9; font-size: 0.8em; letter-spacing: 3px; text-transform: uppercase; }
    
    .space-banner { position: relative; width: 100%; height: 180px; background: #000814; border-radius: 15px; overflow: hidden; border: 1px solid #1b263b; margin-top:10px; }
    .stars { position: absolute; width: 200%; height: 200%; background: url('https://www.transparenttextures.com/patterns/stardust.png'); opacity: 0.9; animation: rotateStars 120s infinite linear; }
    @keyframes rotateStars { from { transform: translate(-25%, -25%) rotate(0deg); } to { transform: translate(-25%, -25%) rotate(360deg); } }
    
    .planet { position: absolute; border-radius: 50%; opacity: 0; animation: fly infinite linear; }
    .p1 { background: radial-gradient(circle, #415a77, #000); width: 14px; height: 14px; animation-duration: 8s; top: 15%; }
    .p2 { background: radial-gradient(circle, #778da9, #1b263b); width: 9px; height: 9px; animation-duration: 6s; animation-delay: 2s; top: 55%; }
    .p3 { background: radial-gradient(circle, #e0e1dd, #415a77); width: 12px; height: 12px; animation-duration: 11s; animation-delay: 4s; top: 35%; }
    .p4 { background: radial-gradient(circle, #ff4b4b, #330000); width: 10px; height: 10px; animation-duration: 7s; animation-delay: 1s; top: 75%; }
    .p5 { background: radial-gradient(circle, #5e60ce, #000); width: 7px; height: 7px; animation-duration: 9s; animation-delay: 5s; top: 45%; }
    
    @keyframes fly { 
        0% { transform: translateX(-100px) scale(0.5); opacity: 0; } 
        15% { opacity: 1; }
        85% { opacity: 1; }
        100% { transform: translateX(1600px) scale(1.8); opacity: 0; } 
    }
    
    .clock-box { position: absolute; bottom: 15px; right: 20px; background: rgba(13,27,42,0.9); padding: 8px 15px; border-radius: 10px; color: white; font-family: monospace; border: 1px solid #415a77; z-index: 10; }
    .moon-altar { background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 100%); border-radius: 20px; padding: 25px; border: 1px solid #415a77; color: #e0e1dd; }
    .widget-title { color:#778da9; font-size: 1.25em; font-weight: 800; margin-bottom: 10px; text-transform: uppercase; }
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

def format_cell(row):
    """Глубокий формат ячейки со всеми данными"""
    lon = row.get('Lon', 0)
    s_idx = int(lon/30)
    # Накшатра
    n_deg = 360/27
    n_idx = int(lon / n_deg) % 27
    # Пада
    p_deg = n_deg / 4
    pada = int((lon % n_deg) / p_deg) + 1
    # Навамша управитель
    nav_idx = int((lon * 9) / 30) % 12
    
    return f"""
    <div style="line-height:1.4;">
        <b>{P_ICONS.get(row['Planet'], row['Planet'])}</b> | {Z_ICONS[ZODIAC_SIGNS[s_idx]]} {row['Deg']:.2f}°<br>
        <span style="color:#e0e1dd; font-size:1.1em;"><b>{NAKSHATRAS[n_idx]}</b> ({NAK_LORDS[n_idx]})</span><br>
        <span style="font-size:0.9em; opacity:0.8;">{NAK_TEXT_SYMBOLS[n_idx]}</span><br>
        <span style="color:#778da9;">Пада {pada} | Управитель: {PADA_LORDS_MAP[nav_idx]}</span>
    </div>
    """

def get_planet_data(t):
    ayan = get_dynamic_ayanamsa(t)
    earth = eph['earth']
    p_map = {'Sun': eph['sun'], 'Moon': eph['moon'], 'Mars': eph['mars'], 'Mercury': eph['mercury'], 'Jupiter': eph['jupiter_barycenter'], 'Venus': eph['venus'], 'Saturn': eph['saturn_barycenter']}
    
    res = []
    for name, obj in p_map.items():
        lon = (earth.at(t).observe(obj).ecliptic_latlon()[1].degrees - ayan) % 360
        res.append({'Planet': name, 'Lon': lon, 'Deg': lon % 30})
    
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    roles = ['AK', 'AmK', 'BK', 'MK', 'PiK', 'GK', 'DK']
    df['Role'] = (roles + ['-']*5)[:len(df)]
    
    # Раху (Расчет через положение Лунного Узла)
    # На 2026-05-14 True Node находится в Водолее (~28°)
    T = (t.tt - 2451545.0) / 36525.0
    ra_mean_lon = (125.04455 - 1934.13618 * T + 0.002075 * T**2) % 360
    ra_sid_lon = (ra_mean_lon - ayan) % 360
    ra_row = pd.DataFrame([{'Planet': 'Rahu', 'Lon': ra_sid_lon, 'Deg': ra_sid_lon % 30, 'Role': '-'}])
    
    return pd.concat([df, ra_row], ignore_index=True)

def get_lunar_full_data(t_now):
    earth = eph['earth']
    def get_diff(t_v):
        s = earth.at(t_v).observe(eph['sun']).ecliptic_latlon()[1].degrees
        m = earth.at(t_v).observe(eph['moon']).ecliptic_latlon()[1].degrees
        return (m - s) % 360

    # Стабильный поиск ближайшего события (сканирование)
    def find_nearest(target):
        curr = t_now.utc_datetime()
        # Сначала грубый поиск шагом в 1 день, потом уточнение
        for d in range(32):
            check_t = ts.utc(curr + timedelta(days=d))
            diff = (get_diff(check_t) - target + 180) % 360 - 180
            if abs(diff) < 15: # Мы близко
                # Уточняем минутным шагом
                sub_curr = check_t.utc_datetime() - timedelta(days=1)
                for m in range(2880):
                    precise_t = ts.utc(sub_curr + timedelta(minutes=m))
                    if precise_t.utc_datetime() < t_now.utc_datetime(): continue
                    p_diff = (get_diff(precise_t) - target + 180) % 360 - 180
                    if abs(p_diff) < 0.1: return precise_t.utc_datetime()
        return curr

    f_dt = find_nearest(180)
    n_dt = find_nearest(0)
    now_diff = get_diff(t_now)
    ayan = get_dynamic_ayanamsa(t_now)
    m_lon = (earth.at(t_now).observe(eph['moon']).ecliptic_latlon()[1].degrees - ayan) % 360

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

def find_rotations(start_dt):
    events = []
    t_start = ts.utc(start_dt.year, start_dt.month, start_dt.day, start_dt.hour, start_dt.minute)
    df_now = get_planet_data(t_start)
    current_pair = f"{df_now.iloc[0]['Planet']}-{df_now.iloc[1]['Planet']}"
    
    # Назад
    for i in range(1, 1000):
        t_check = start_dt - timedelta(minutes=i*10)
        df_p = get_planet_data(ts.utc(t_check.year, t_check.month, t_check.day, t_check.hour, t_check.minute))
        if f"{df_p.iloc[0]['Planet']}-{df_p.iloc[1]['Planet']}" != current_pair:
            events.append({"type": "Предыдущая", "dt": t_check + timedelta(hours=3), "ak": df_p.iloc[0], "amk": df_p.iloc[1]})
            break
    # Вперед
    for i in range(1, 1000):
        t_check = start_dt + timedelta(minutes=i*10)
        df_f = get_planet_data(ts.utc(t_check.year, t_check.month, t_check.day, t_check.hour, t_check.minute))
        if f"{df_f.iloc[0]['Planet']}-{df_f.iloc[1]['Planet']}" != current_pair:
            events.append({"type": "Следующая", "dt": t_check + timedelta(hours=3), "ak": df_f.iloc[0], "amk": df_f.iloc[1]})
            break
    return events

# ============================================================
# ⛔ БЛОК 3: ИНТЕРФЕЙС
# ============================================================
components.html("<script>setInterval(()=>{let d=new Date();let s=new Date(d.getTime()+(d.getTimezoneOffset()*60000)+(3600000*3)).toTimeString().split(' ')[0];window.parent.document.getElementById('live-clock').innerHTML=s;},1000);</script>", height=0)
t1, t2 = st.tabs(["📊 Прямой эфир", "📅 Планировщик ротаций"])

with t1:
    now_u = datetime.utcnow()
    t_n = ts.utc(now_u.year, now_u.month, now_u.day, now_u.hour, now_u.minute)
    df_n = get_planet_data(t_n)
    l = get_lunar_full_data(t_n)
    
    # ЛУННЫЙ АЛТАРЬ
    st.markdown(f"""
    <div class="moon-altar">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div><div style="font-size: 4em; line-height:1;">{l['phase_icon']}</div><div style="font-size: 1.8em; font-weight: bold;">{l['tithi']} лунные сутки</div></div>
            <div style="text-align: right;"><div style="font-size: 1.4em; font-weight: bold;">{l['sign']}</div><div style="color: #778da9;">{l['nak']}</div></div>
        </div>
        <div style="margin: 15px 0 5px 0;">
            <small style="color:#778da9; text-transform: uppercase;">Освещенность Луны: {int(l['illum'])}%</small>
            <div style="background: rgba(255,255,255,0.1); height: 12px; border-radius: 6px; margin-top:5px;">
                <div style="background: linear-gradient(to right, #415a77, #e0e1dd); width: {l['illum']}%; height: 12px; border-radius: 6px; box-shadow: 0 0 10px #fff;"></div>
            </div>
        </div>
        <div style="display: flex; justify-content: space-between; font-size: 0.9em; margin-top: 20px; border-top: 1px solid rgba(255,255,255,0.1); padding-top:15px;">
            <div>🌕 <b>Осталось до Полнолуния:</b><br>{l['rem_full'].days}д {l['rem_full'].seconds//3600}ч ({l['full_dt'].strftime('%d.%m %H:%M')})</div>
            <div style="text-align: right;">🌑 <b>Осталось до Новолуния:</b><br>{l['rem_new'].days}д {l['rem_new'].seconds//3600}ч ({l['new_dt'].strftime('%d.%m %H:%M')})</div>
        </div>
    </div>""", unsafe_allow_html=True)

    # АК и AmK
    st.subheader("👑 Текущие АК и АмК")
    c1, c2 = st.columns(2)
    with c1: st.markdown(f'<div class="custom-metric-box"><div class="widget-title">💎 ТЕКУЩАЯ АК</div>{format_cell(df_n.iloc[0])}</div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="custom-metric-box"><div class="widget-title">🥈 ТЕКУЩАЯ AmK</div>{format_cell(df_n.iloc[1])}</div>', unsafe_allow_html=True)

    # РОТАЦИИ
    st.subheader("🔄 Ближайшие смены ротаций")
    rots = find_rotations(now_u)
    rc1, rc2 = st.columns(2)
    for r in rots:
        with (rc1 if r['type']=="Предыдущая" else rc2):
            st.markdown(f"""<div class="custom-metric-box" style="background:rgba(255,255,255,0.03)">
                <div class="widget-title">{r['type'].upper()} ({r['dt'].strftime('%H:%M')})</div>
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px;">
                    <div><small style="color:#778da9">АК</small><br>{format_cell(r['ak'])}</div>
                    <div><small style="color:#778da9">AmK</small><br>{format_cell(r['amk'])}</div>
                </div>
            </div>""", unsafe_allow_html=True)

    # ТАБЛИЦА
    st.subheader("📋 Полная таблица карак")
    df_v = df_n.copy()
    df_v['Детализация'] = df_v.apply(format_cell, axis=1)
    st.write(df_v[['Role', 'Planet', 'Deg', 'Детализация']].to_html(escape=False, index=False), unsafe_allow_html=True)

    # РАХУ
    st.subheader("🐉 Мониторинг Раху")
    ra_val = df_n[df_n['Planet'] == 'Rahu'].iloc[0]
    cr1, cr2 = st.columns([1, 2])
    with cr1: st.markdown(f'<div class="custom-metric-box" style="border-color:#ff4b4b;"><div class="widget-title">ТЕКУЩИЙ РАХУ</div>{format_cell(ra_val)}</div>', unsafe_allow_html=True)
    with cr2: st.markdown("""<div style="font-size:0.9em; padding:20px; background:rgba(255,75,75,0.05); border-radius:12px; border:1px solid #ff4b4b;">
        <b>Календарь ингрессий Раху (True Node):</b><br>
        • Рыбы: до 18.05.2025<br>
        • <b>Водолей: с 18.05.2025 по 05.12.2026</b><br>
        • Козерог: с 05.12.2026<br><br>
        <small><i>* Раху движется ретроградно. Сейчас он в конце Водолея, направляется к Козерогу.</i></small>
    </div>""", unsafe_allow_html=True)

with t2:
    st.subheader("⚙️ Сетка ротаций")
    cx, cy = st.columns(2)
    with cx: ds = st.date_input("Начало", datetime.now()); ts_i = st.time_input("Старт", time(0, 0))
    with cy: de = st.date_input("Конец", datetime.now() + timedelta(days=2)); te_i = st.time_input("Финиш", time(23, 59))
    
    if st.button("🚀 ПОСТРОИТЬ ГРАФИК"):
        s_u = datetime.combine(ds, ts_i) - timedelta(hours=3)
        e_u = datetime.combine(de, te_i) - timedelta(hours=3)
        results = []; curr = s_u
        
        df_init = get_planet_data(ts.utc(curr.year, curr.month, curr.day, curr.hour, curr.minute))
        last_p = f"{df_init.iloc[0]['Planet']}-{df_init.iloc[1]['Planet']}"
        
        while curr < e_u:
            curr += timedelta(minutes=5)
            t_ev = ts.utc(curr.year, curr.month, curr.day, curr.hour, curr.minute)
            df_ev = get_planet_data(t_ev)
            new_p = f"{df_ev.iloc[0]['Planet']}-{df_ev.iloc[1]['Planet']}"
            
            if new_p != last_p:
                results.append({
                    "Дата": (curr + timedelta(hours=3)).strftime("%d.%m.%Y"),
                    "Время": (curr + timedelta(hours=3)).strftime("%H:%M"),
                    "💎 АК": format_cell(df_ev.iloc[0]),
                    "🥈 AmK": format_cell(df_ev.iloc[1])
                })
                last_p = new_p
        
        if results:
            st.write(pd.DataFrame(results).to_html(escape=False, index=False), unsafe_allow_html=True)
