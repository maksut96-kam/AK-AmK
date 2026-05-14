import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta, time
import pandas as pd
import streamlit.components.v1 as components
import math
import base64

# ============================================================
# ⛔ БЛОК 1: КОНФИГУРАЦИЯ
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
NAK_TEXT_SYMBOLS = ["Голова лошади, всадник, карета", "Йони, женские органы, лодка", "Лезвие, бритва, нож, пламя", "Повозка, колесница, храм, дерево", "Голова оленя, горшок с сомой", "Слеза, алмаз, человеческая голова", "Лук, колчан стрел, дом", "Вымя коровы, цветок лотоса, круг", "Свернувшаяся змея, колесо", "Трон, паланкин, корона", "Передние ножки кровати, гамак", "Задние ножки кровати, посох", "Ладонь, сжатый кулак, гончарный круг", "Сверкающая жемчужина, драгоценный камень", "Побег растения, коралл, меч", "Триумфальная арка, гончарный круг", "Посох, лотос, триумфальная арка", "Круглый амулет, зонтик, серьга", "Связка корней, стрекало для слона", "Веер, ложе, сито для веяния зерна", "Бивень слона, маленькая кровать", "Ухо, три следа, трезубец", "Барабан, флейта, корона", "Пустой круг, тысяча цветов", "Двуликий человек, меч, передние ножки", "Близнецы, змея, задние ножки", "Рыба, барабан"]
RU_DAYS = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]
PADA_LORDS_MAP = ["Марс", "Венера", "Меркурий", "Луна", "Солнце", "Меркурий", "Венера", "Марс", "Юпитер", "Сатурн", "Сатурн", "Юпитер"]
P_ICONS = {'Sun': '☀️ Sun', 'Moon': '🌙 Moon', 'Mars': '🔴 Mars', 'Mercury': '☿️ Merc', 'Jupiter': '🔵 Jup', 'Venus': '♀️ Venus', 'Saturn': '🪐 Sat'}
Z_ICONS = {"Овен": "♈ Овен", "Телец": "♉ Телец", "Близнецы": "♊ Близн", "Рак": "♋ Рак", "Лев": "♌ Лев", "Дева": "♍ Дева", "Весы": "♎ Весы", "Скорпион": "♏ Скорп", "Стрелец": "♐ Стрел", "Козерог": "♑ Козег", "Водолей": "♒ Водол", "Рыбы": "♓ Рыбы"}

st.markdown("""
<style>
    .header-box { margin-bottom: 5px; }
    .main-title { font-family: 'Lexend', sans-serif; font-weight: 800; font-size: 2.2em; color: white; margin-bottom: 0; }
    .sub-title { color: #778da9; font-size: 0.8em; letter-spacing: 3px; text-transform: uppercase; margin-bottom: 15px; }
    .space-banner { position: relative; width: 100%; height: 180px; background: #000; border-radius: 15px; overflow: hidden; border: 1px solid #1b263b; }
    .stars { position: absolute; width: 100%; height: 100%; background: url('https://www.transparenttextures.com/patterns/stardust.png'); opacity: 0.4; }
    .planet-container { position: absolute; top: 50%; left: 50%; width: 1px; height: 1px; }
    .planet { position: absolute; border-radius: 50%; opacity: 0; animation: fly 5s infinite linear; }
    .p1 { background: radial-gradient(circle, #415a77, #0d1b2a); width: 15px; height: 15px; animation-duration: 6s; }
    .p2 { background: radial-gradient(circle, #778da9, #415a77); width: 10px; height: 10px; animation-duration: 4s; animation-delay: 1.5s; }
    @keyframes fly { 0% { transform: scale(0.1) translate(0, 0); opacity: 0; } 20% { opacity: 1; } 100% { transform: scale(18) translate(150px, 80px); opacity: 0; } }
    .clock-box { position: absolute; bottom: 15px; right: 20px; background: rgba(13,27,42,0.8); padding: 8px 15px; border-radius: 10px; color: white; font-family: monospace; border: 1px solid #415a77; }
    .moon-altar { background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 100%); border-radius: 20px; padding: 25px; border: 1px solid #415a77; color: #e0e1dd; }
    .custom-metric-box { background: rgba(65, 90, 119, 0.2); padding: 15px; border-radius: 12px; border: 1px solid #778da9; height: 100%; }
    .small-metric { background: rgba(0,0,0,0.2); padding: 10px; border-radius: 8px; border: 1px solid #415a77; font-size: 0.85em; margin-top: 10px; }
</style>

<div class="header-box">
    <h1 class="main-title">JULIA ASSISTANT</h1>
    <div class="sub-title">Astro coordination center</div>
</div>

<div class="space-banner">
    <div class="stars"></div>
    <div class="planet-container"><div class="planet p1"></div><div class="planet p2"></div></div>
    <div class="clock-box" id="live-clock">00:00:00</div>
</div>
""", unsafe_allow_html=True)

components.html("<script>setInterval(()=>{let d=new Date();let s=new Date(d.getTime()+(d.getTimezoneOffset()*60000)+(3600000*3)).toTimeString().split(' ')[0];window.parent.document.getElementById('live-clock').innerHTML=s;},1000);</script>", height=0)

# ============================================================
# ⛔ БЛОК 2: РАСЧЕТЫ
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
    ra_lon = (earth.at(t).observe(eph['moon']).ecliptic_latlon()[1].degrees - ayan + 180) % 360 
    ra_row = pd.DataFrame([{'Planet': 'Rahu', 'Lon': ra_lon, 'Deg': 30 - (ra_lon % 30), 'Role': '-'}])
    return pd.concat([df, ra_row], ignore_index=True)

def get_lunar_data(t):
    earth = eph['earth']
    s = earth.at(t).observe(eph['sun']).ecliptic_latlon()[1].degrees
    m = earth.at(t).observe(eph['moon']).ecliptic_latlon()[1].degrees
    diff = (m - s) % 360
    ayan = get_dynamic_ayanamsa(t)
    lon_sid = (m - ayan) % 360
    s_idx = int(lon_sid / 30)
    n_idx = int(lon_sid / (360/27)) % 27
    return {
        "tithi": math.ceil(diff / 12) or 1,
        "phase": ["🌑","🌒","🌓","🌔","🌕","🌖","🌗","🌘"][int(((diff + 22.5) % 360) / 45)],
        "illum": (1 - math.cos(math.radians(diff))) / 2 * 100,
        "sign": ZODIAC_SIGNS[s_idx], "nak": NAKSHATRAS[n_idx], "lord": NAK_LORDS[n_idx],
        "wax": diff < 180,
        "to_full": ((180 - diff) % 360) / 0.508, "to_new": ((360 - diff) % 360) / 0.508
    }

def format_cell(row):
    lon = row.get('Lon', 0)
    s_idx = int(lon/30)
    n_idx = int(lon / (360/27)) % 27
    pada = int((lon % (360/27)) / (360/108)) + 1
    nav_idx = int((lon * 9) / 30) % 12
    return f"<b>{P_ICONS.get(row['Planet'], row['Planet'])}</b> | {Z_ICONS[ZODIAC_SIGNS[s_idx]]} {row['Deg']:.2f}°<br><b>{NAKSHATRAS[n_idx]}</b> ({NAK_LORDS[n_idx]})<br>{NAK_TEXT_SYMBOLS[n_idx]}<br>Пада {pada} | Упр: {PADA_LORDS_MAP[nav_idx]}"

def find_rotations(start_dt, hours_back=48, hours_fwd=48):
    events = []
    # Поиск назад
    curr = start_dt
    df_now = get_planet_data(ts.utc(curr.year, curr.month, curr.day, curr.hour, curr.minute))
    last_p = f"{df_now.iloc[0]['Planet']}-{df_now.iloc[1]['Planet']}"
    
    # Назад
    for i in range(1, hours_back * 12):
        check = start_dt - timedelta(minutes=i*5)
        df_c = get_planet_data(ts.utc(check.year, check.month, check.day, check.hour, check.minute))
        pair = f"{df_c.iloc[0]['Planet']}-{df_c.iloc[1]['Planet']}"
        if pair != last_p:
            events.append({"type": "Предыдущая", "dt": check + timedelta(hours=3), "ak": df_c.iloc[0], "amk": df_c.iloc[1]})
            break
            
    # Вперед
    for i in range(1, hours_fwd * 12):
        check = start_dt + timedelta(minutes=i*5)
        df_c = get_planet_data(ts.utc(check.year, check.month, check.day, check.hour, check.minute))
        pair = f"{df_c.iloc[0]['Planet']}-{df_c.iloc[1]['Planet']}"
        if pair != last_p:
            events.append({"type": "Следующая", "dt": check + timedelta(hours=3), "ak": df_c.iloc[0], "amk": df_c.iloc[1]})
            break
    return events

# ============================================================
# ⛔ БЛОК 3: ИНТЕРФЕЙС
# ============================================================
t1, t2 = st.tabs(["📊 Прямой эфир", "📅 Планировщик ротаций"])

with t1:
    now = datetime.utcnow()
    t_n = ts.utc(now.year, now.month, now.day, now.hour, now.minute, now.second)
    df_n = get_planet_data(t_n)
    l = get_lunar_data(t_n)
    
    st.markdown(f"""
    <div class="moon-altar">
        <div style="display: flex; justify-content: space-between;">
            <div><div style="font-size: 3.5em;">{l['phase']}</div><div style="font-size: 1.8em; font-weight: bold;">{l['tithi']} лунные сутки</div>
            <div style="color: #778da9;">{"Растущая" if l['wax'] else "Убывающая"} • {int(l['illum'])}% света</div></div>
            <div style="text-align: right;"><div style="font-size: 1.2em; font-weight: bold;">{l['sign']}</div><div style="color: #778da9;">{l['nak']} ({l['lord']})</div></div>
        </div>
        <div style="background: rgba(255,255,255,0.1); height: 8px; border-radius: 4px; margin: 15px 0;"><div style="background: #e0e1dd; width: {l['illum']}%; height: 8px; border-radius: 4px;"></div></div>
        <div style="display: flex; justify-content: space-between; font-size: 0.85em;"><span>🌕 Полнолуние: {int(l['to_full']//24)}д {int(l['to_full']%24)}ч</span><span>🌑 Новолуние: {int(l['to_new']//24)}д {int(l['to_new']%24)}ч</span></div>
    </div>""", unsafe_allow_html=True)

    st.subheader("👑 Текущие АК и АмК")
    c1, c2 = st.columns(2)
    with c1: st.markdown(f'<div class="custom-metric-box"><div style="color:#778da9; font-size:0.8em; font-weight:bold; margin-bottom:5px;">💎 АК (Атма-карака)</div>{format_cell(df_n.iloc[0])}</div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="custom-metric-box"><div style="color:#778da9; font-size:0.8em; font-weight:bold; margin-bottom:5px;">🥈 AmK (Аматья-карака)</div>{format_cell(df_n.iloc[1])}</div>', unsafe_allow_html=True)

    # Динамика ротаций
    st.subheader("🔄 Ближайшие смены ротаций")
    rots = find_rotations(now)
    rc1, rc2 = st.columns(2)
    for r in rots:
        with (rc1 if r['type']=="Предыдущая" else rc2):
            st.markdown(f"""<div class="small-metric">
                <b>{r['type']} ротация:</b> {r['dt'].strftime('%d.%m %H:%M')}<br>
                <span style="color:#778da9">АК: {r['ak']['Planet']} | AmK: {r['amk']['Planet']}</span>
            </div>""", unsafe_allow_html=True)

    st.subheader("📋 Таблица карак")
    df_f = df_n.copy()
    df_f['Инфо'] = df_f.apply(format_cell, axis=1)
    st.write(df_f[['Role', 'Planet', 'Deg', 'Инфо']].to_html(escape=False, index=False), unsafe_allow_html=True)

with t2:
    st.subheader("⚙️ Расчет сетки")
    cx, cy = st.columns(2)
    with cx:
        ds = st.date_input("Начало", datetime.now())
        ts_i = st.time_input("Старт", time(0, 0))
    with cy:
        de = st.date_input("Конец", datetime.now() + timedelta(days=2))
        te_i = st.time_input("Финиш", time(23, 59))

    if st.button("🚀 ЗАПУСТИТЬ РАСЧЕТ"):
        start_u = datetime.combine(ds, ts_i) - timedelta(hours=3)
        end_u = datetime.combine(de, te_i) - timedelta(hours=3)
        pb = st.progress(0); status_txt = st.empty(); results = []
        curr = start_u; total_delta = (end_u - start_u).total_seconds()
        
        df_init = get_planet_data(ts.utc(curr.year, curr.month, curr.day, curr.hour, curr.minute))
        last_pair = f"{df_init.iloc[0]['Planet']}-{df_init.iloc[1]['Planet']}"
        results.append({"Дата": (curr + timedelta(hours=3)).strftime("%d.%m.%Y"), "День": RU_DAYS[(curr + timedelta(hours=3)).weekday()], "Время": (curr + timedelta(hours=3)).strftime("%H:%M"), "💎 АК": format_cell(df_init.iloc[0]), "🥈 AmK": format_cell(df_init.iloc[1])})

        while curr < end_u:
            curr += timedelta(minutes=5)
            pb.progress(min(1.0, (curr - start_u).total_seconds() / total_delta))
            t_eval = ts.utc(curr.year, curr.month, curr.day, curr.hour, curr.minute)
            df_eval = get_planet_data(t_eval)
            new_pair = f"{df_eval.iloc[0]['Planet']}-{df_eval.iloc[1]['Planet']}"
            if new_pair != last_pair:
                results.append({"Дата": (curr + timedelta(hours=3)).strftime("%d.%m.%Y"), "День": RU_DAYS[(curr + timedelta(hours=3)).weekday()], "Время": (curr + timedelta(hours=3)).strftime("%H:%M"), "💎 АК": format_cell(df_eval.iloc[0]), "🥈 AmK": format_cell(df_eval.iloc[1])})
                last_pair = new_pair
        pb.empty(); status_txt.success("Готово!")
        
        if results:
            df_res = pd.DataFrame(results)
            html_table = df_res.to_html(escape=False, index=False).replace('\n', '')
            
            # ИСПРАВЛЕННЫЙ БЛОК ПЕЧАТИ (КОДИРОВКА UTF-8)
            print_code = f"""
            <script>
            function openPrint() {{
                const html = `<!DOCTYPE html><html><head>
                <meta charset="UTF-8">
                <title>Astro Report</title>
                <style>
                    body {{ font-family: sans-serif; padding: 20px; }}
                    table {{ border-collapse: collapse; width: 100%; }}
                    th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; font-size: 11px; }}
                    th {{ background: #f4f4f4; }}
                </style></head>
                <body><h2>График ротаций АК/AmK</h2>{html_table}</body></html>`;
                
                const blob = new Blob([html], {{type: 'text/html;charset=utf-8'}});
                const url = URL.createObjectURL(blob);
                window.open(url, '_blank');
            }}
            </script>
            <button onclick="openPrint()" style="width:100%; padding:15px; background:#28a745; color:white; border:none; border-radius:10px; cursor:pointer; font-weight:bold; margin-bottom:20px;">
                🖨️ ПЕЧАТАТЬ ТАБЛИЦУ (БЕЗ ОШИБОК КОДИРОВКИ)
            </button>
            """
            components.html(print_code, height=70)
            st.write(df_res.to_html(escape=False, index=False), unsafe_allow_html=True)
