import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta, time
import pandas as pd
import streamlit.components.v1 as components
import math
import base64

# ============================================================
# ⛔ БЛОК 1: ДВИЖОК И СТИЛИЗАЦИЯ
# ============================================================
st.set_page_config(page_title="Julia Assistant Astro Pro", layout="wide")

@st.cache_resource
def init_engine():
    ts = load.timescale()
    eph = load('de421.bsp')
    return ts, eph

ts, eph = init_engine()

# --- СЛОВАРИ (ПОЛНЫЕ) ---
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = ["Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Аридра", "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-пх", "Уттара-пх", "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьештха", "Мула", "Пурва-аш", "Уттара-аш", "Шравана", "Дхаништха", "Шатабхиша", "Пурва-бх", "Уттара-бх", "Ревати"]
NAK_LORDS = ["Кету", "Венера", "Солнце", "Луна", "Марс", "Раху", "Юпитер", "Сатурн", "Меркурий"] * 3
NAK_TEXT_SYMBOLS = ["Голова лошади, всадник, карета", "Йони, женские органы, лодка", "Лезвие, бритва, нож, пламя", "Повозка, колесница, храм, дерево", "Голова оленя, горшок с сомой", "Слеза, алмаз, человеческая голова", "Лук, колчан стрел, дом", "Вымя коровы, цветок лотоса, круг", "Свернувшаяся змея, колесо", "Трон, паланкин, корона", "Передние ножки кровати, гамак", "Задние ножки кровати, посох", "Ладонь, сжатый кулак, гончарный круг", "Сверкающая жемчужина, драгоценный камень", "Побег растения, коралл, меч", "Триумфальная арка, гончарный круг", "Посох, лотос, триумфальная арка", "Круглый амулет, зонтик, серьга", "Связка корней, стрекало для слона", "Веер, ложе, сито для веяния зерна", "Бивень слона, маленькая кровать", "Ухо, три следа, трезубец", "Барабан, флейта, корона", "Пустой круг, тысяча цветов", "Двуликий человек, меч, передние ножки", "Близнецы, змея, задние ножки", "Рыба, барабан"]
RU_DAYS = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]
PADA_LORDS_MAP = ["Марс", "Венера", "Меркурий", "Луна", "Солнце", "Меркурий", "Венера", "Марс", "Юпитер", "Сатурн", "Сатурн", "Юпитер"]
P_ICONS = {'Sun': '☀️ Sun', 'Moon': '🌙 Moon', 'Mars': '🔴 Mars', 'Mercury': '☿️ Merc', 'Jupiter': '🔵 Jup', 'Venus': '♀️ Venus', 'Saturn': '🪐 Sat'}
Z_ICONS = {"Овен": "♈ Овен", "Телец": "♉ Телец", "Близнецы": "♊ Близн", "Рак": "♋ Рак", "Лев": "♌ Лев", "Дева": "♍ Дева", "Весы": "♎ Весы", "Скорпион": "♏ Скорп", "Стрелец": "♐ Стрел", "Козерог": "♑ Козег", "Водолей": "♒ Водол", "Рыбы": "♓ Рыбы"}

# --- CSS ДЛЯ ЛЕТАЮЩИХ ПЛАНЕТ И ИНТЕРФЕЙСА ---
st.markdown("""
<style>
    .header-area { display: flex; align-items: center; margin-bottom: 10px; }
    .main-title { font-family: 'Lexend', sans-serif; font-weight: 800; font-size: 2.2em; color: white; margin: 0; }
    
    .space-banner { position: relative; width: 100%; height: 250px; background: #000; border-radius: 20px; overflow: hidden; border: 1px solid #1b263b; }
    .stars { position: absolute; width: 100%; height: 100%; background: url('https://www.transparenttextures.com/patterns/stardust.png'); opacity: 0.5; }
    
    .planet-container { position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 10px; height: 10px; }
    .planet { position: absolute; border-radius: 50%; opacity: 0; animation: fly 4s infinite linear; }
    .p1 { background: radial-gradient(circle, #415a77, #0d1b2a); width: 20px; height: 20px; animation-duration: 6s; }
    .p2 { background: radial-gradient(circle, #778da9, #415a77); width: 15px; height: 15px; animation-duration: 4s; animation-delay: 1s; }
    .p3 { background: radial-gradient(circle, #e0e1dd, #778da9); width: 10px; height: 10px; animation-duration: 8s; animation-delay: 2s; }
    
    @keyframes fly {
        0% { transform: scale(0.1) translate(0, 0); opacity: 0; }
        20% { opacity: 1; }
        100% { transform: scale(15) translate(100px, 50px); opacity: 0; }
    }
    
    .clock-box { position: absolute; bottom: 15px; right: 20px; background: rgba(13,27,42,0.8); padding: 8px 15px; border-radius: 10px; color: white; font-family: monospace; border: 1px solid #415a77; z-index: 10; }
    .moon-altar { background: linear-gradient(135deg, #0d1b2a 0%, #1b263b 100%); border-radius: 20px; padding: 20px; border: 1px solid #415a77; color: #e0e1dd; }
    .custom-metric-box { background: rgba(65, 90, 119, 0.2); padding: 15px; border-radius: 12px; border: 1px solid #778da9; height: 100%; }
</style>

<div class="header-area">
    <div><h1 class="main-title">JULIA ASSISTANT PRO</h1><div style="color:#778da9; letter-spacing:4px; font-size:0.7em;">ASTRO INTELLIGENCE SYSTEM</div></div>
</div>

<div class="space-banner">
    <div class="stars"></div>
    <div class="planet-container"><div class="planet p1"></div><div class="planet p2"></div><div class="planet p3"></div></div>
    <div class="clock-box" id="live-clock">00:00:00</div>
</div>
""", unsafe_allow_html=True)

components.html("<script>setInterval(()=>{let d=new Date();let s=new Date(d.getTime()+(d.getTimezoneOffset()*60000)+(3600000*3)).toTimeString().split(' ')[0];window.parent.document.getElementById('live-clock').innerHTML=s;},1000);</script>", height=0)

# ============================================================
# ⛔ БЛОК 2: ЛОГИКА
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
    df['Role'] = (['AK', 'AmK', 'BK', 'MK', 'PiK', 'GK', 'DK'] + ['-']*5)[:len(df)]
    ra_lon = (earth.at(t).observe(eph['moon']).ecliptic_latlon()[1].degrees - ayan + 180) % 360 
    ra_row = pd.DataFrame([{'Planet': 'Rahu', 'Lon': ra_lon, 'Deg': 30 - (ra_lon % 30), 'Role': '-'}])
    return pd.concat([df, ra_row], ignore_index=True)

def get_lunar_info(t):
    earth = eph['earth']
    s = earth.at(t).observe(eph['sun']).ecliptic_latlon()[1].degrees
    m = earth.at(t).observe(eph['moon']).ecliptic_latlon()[1].degrees
    diff = (m - s) % 360
    ayan = get_dynamic_ayanamsa(t)
    lon_sid = (m - ayan) % 360
    s_idx = int(lon_sid / 30)
    n_idx = int(lon_sid / (360/27)) % 27
    d_sign = lon_sid % 30
    gand = "Реактивная (вода/огонь)" if (s_idx in [3,7,11] and d_sign > 27) or (s_idx in [0,4,8] and d_sign < 3) else ""
    return {
        "tithi": math.ceil(diff / 12) or 1,
        "phase": ["🌑","🌒","🌓","🌔","🌕","🌖","🌗","🌘"][int(((diff + 22.5) % 360) / 45)],
        "illum": (1 - math.cos(math.radians(diff))) / 2 * 100,
        "sign": ZODIAC_SIGNS[s_idx], "nak": NAKSHATRAS[n_idx], "lord": NAK_LORDS[n_idx],
        "wax": diff < 180, "gandanta": gand,
        "to_full": ((180 - diff) % 360) / 0.508, "to_new": ((360 - diff) % 360) / 0.508
    }

def get_full_cell(row):
    lon = row['Lon']
    s_idx = int(lon/30)
    n_idx = int(lon / (360/27)) % 27
    pada = int((lon % (360/27)) / (360/108)) + 1
    nav_idx = int((lon * 9) / 30) % 12
    return f"{P_ICONS.get(row['Planet'], row['Planet'])} | {Z_ICONS[ZODIAC_SIGNS[s_idx]]} {row['Deg']:.2f}°<br><b>{NAKSHATRAS[n_idx]}</b> ({NAK_LORDS[n_idx]})<br>{NAK_TEXT_SYMBOLS[n_idx]}<br>Пада {pada} | Упр: {PADA_LORDS_MAP[nav_idx]}"

# ============================================================
# ⛔ БЛОК 3: ТАБЫ
# ============================================================
tab1, tab2 = st.tabs(["📊 Прямой эфир", "📅 Планировщик ротаций"])

with tab1:
    now = datetime.utcnow()
    t_now = ts.utc(now.year, now.month, now.day, now.hour, now.minute, now.second)
    df_n = get_planet_data(t_now)
    l = get_lunar_info(t_now)
    
    st.markdown(f"""
    <div class="moon-altar">
        <div style="display: flex; justify-content: space-between;">
            <div><div style="font-size: 3.5em;">{l['phase']}</div><div style="font-size: 1.8em; font-weight: 700;">{l['tithi']} лунные сутки</div>
            <div style="color: #778da9;">{"Растущая" if l['wax'] else "Убывающая"} • {int(l['illum'])}% света</div></div>
            <div style="text-align: right;"><div style="font-size: 1.2em; font-weight: bold;">{l['sign']}</div><div style="color: #778da9;">{l['nak']} (Лорд: {l['lord']})</div></div>
        </div>
        <div style="background: rgba(255,255,255,0.1); height: 8px; border-radius: 4px; margin: 15px 0;"><div style="background: #e0e1dd; width: {l['illum']}%; height: 8px; border-radius: 4px;"></div></div>
        <div style="display: flex; justify-content: space-between; font-size: 0.85em;"><span>🌕 Полнолуние: {int(l['to_full']//24)}д</span><span>🌑 Новолуние: {int(l['to_new']//24)}д</span></div>
        {"<div style='color:#ff4b4b; margin-top:10px;'>⚠️ ГАНДАНТА: " + l['gandanta'] + "</div>" if l['gandanta'] else ""}
    </div>""", unsafe_allow_html=True)

    st.subheader("👑 Мониторинг ротаций АК/AmK")
    c1, c2 = st.columns(2)
    with c1: st.markdown(f'<div class="custom-metric-box"><div style="color:#778da9; font-size:0.8em; font-weight:bold;">💎 АК (Атма-карака)</div>{get_full_cell(df_n.iloc[0])}</div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="custom-metric-box"><div style="color:#778da9; font-size:0.8em; font-weight:bold;">🥈 AmK (Аматья-карака)</div>{get_full_cell(df_n.iloc[1])}</div>', unsafe_allow_html=True)

    r_deg = df_n[df_n['Planet']=='Rahu'].iloc[0]['Deg']
    st.info(f"🐲 **Монитор Раху:** {r_deg:.2f}° (Зона: {'⚠️ Критическая' if r_deg < 2 or r_deg > 28 else '✅ Стабильная'})")

with tab2:
    st.subheader("⚙️ Расчет сетки ротаций")
    col1, col2 = st.columns(2)
    with col1:
        d_s = st.date_input("Начало", datetime.now())
        t_s = st.time_input("Время старта", time(0, 0))
    with col2:
        d_e = st.date_input("Конец", datetime.now() + timedelta(days=2))
        t_e = st.time_input("Время конца", time(23, 59))

    if st.button("🚀 РАССЧИТАТЬ ГРАФИК РОТАЦИЙ"):
        start = datetime.combine(d_s, t_s) - timedelta(hours=3)
        end = datetime.combine(d_e, t_e) - timedelta(hours=3)
        
        prog = st.progress(0)
        status = st.empty()
        events = []
        
        curr = start
        total = (end - start).total_seconds()
        
        df_init = get_planet_data(ts.utc(curr.year, curr.month, curr.day, curr.hour, curr.minute))
        last_p = f"{df_init.iloc[0]['Planet']}-{df_init.iloc[1]['Planet']}"
        
        events.append({"Дата": (curr + timedelta(hours=3)).strftime("%d.%m.%Y"), "День": RU_DAYS[(curr + timedelta(hours=3)).weekday()], "Время": (curr + timedelta(hours=3)).strftime("%H:%M"), "💎 АК": get_full_cell(df_init.iloc[0]), "🥈 AmK": get_full_cell(df_init.iloc[1])})

        while curr < end:
            curr += timedelta(minutes=5)
            prog.progress(min(1.0, (curr - start).total_seconds() / total))
            status.text(f"Сканирование: {curr.strftime('%d.%m %H:%M')}")
            
            t_loop = ts.utc(curr.year, curr.month, curr.day, curr.hour, curr.minute)
            df_loop = get_planet_data(t_loop)
            new_p = f"{df_loop.iloc[0]['Planet']}-{df_loop.iloc[1]['Planet']}"
            
            if new_p != last_p:
                events.append({"Дата": (curr + timedelta(hours=3)).strftime("%d.%m.%Y"), "День": RU_DAYS[(curr + timedelta(hours=3)).weekday()], "Время": (curr + timedelta(hours=3)).strftime("%H:%M"), "💎 АК": get_full_cell(df_loop.iloc[0]), "🥈 AmK": get_full_cell(df_loop.iloc[1])})
                last_p = new_p
        
        prog.empty()
        status.success("✅ Сетка ротаций построена!")
        
        if events:
            df_res = pd.DataFrame(events)
            table_html = df_res.to_html(escape=False, index=False).replace('"', '\\"')
            
            # --- ХИТРЫЙ МЕХАНИЗМ ПЕЧАТИ ЧЕРЕЗ JS ---
            print_script = f"""
            <script>
            function printData() {{
                var win = window.open('', '_blank');
                win.document.write('<html><head><title>Astro Print</title>');
                win.document.write('<style>table {{ border-collapse: collapse; width: 100%; font-family: sans-serif; }} th, td {{ border: 1px solid #ccc; padding: 10px; text-align: left; font-size: 12px; }} th {{ background: #f0f0f0; }}</style>');
                win.document.write('</head><body>');
                win.document.write('<h2>График ротаций АК/AmK</h2>');
                win.document.write("{table_html}");
                win.document.write('</body></html>');
                win.document.close();
                win.print();
            }}
            </script>
            <button onclick="printData()" style="width:100%; padding:15px; background:#00C853; color:white; border:none; border-radius:10px; cursor:pointer; font-weight:bold; font-size:1.1em;">
                🖨️ ОТКРЫТЬ И РАСПЕЧАТАТЬ ТАБЛИЦУ
            </button>
            """
            components.html(print_script, height=70)
            st.write(df_res.to_html(escape=False, index=False), unsafe_allow_html=True)
