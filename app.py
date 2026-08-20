import swisseph as swe
import streamlit as st
from skyfield.api import load
from datetime import datetime, timedelta, time
import pandas as pd
import streamlit.components.v1 as components
import math
import base64
import google.generativeai as genai

def get_image_base64(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return "" 

# ============================================================
# ⛔ БЛОК 1: КОНФИГУРАЦИЯ И СТИЛИ
# ============================================================
st.set_page_config(page_title="Julia Assistant", layout="wide")

# --- ИНТЕГРАЦИЯ ВИДЕО-ФОНА (С идеальной читаемостью текста) ---
def add_video_background(video_path="space_background.mp4"):
    try:
        with open(video_path, "rb") as f:
            video_bytes = f.read()
        b64_video = base64.b64encode(video_bytes).decode()
        
        video_html = f"""
        <style>
            /* 1. Главный фон страницы — прозрачный */
            .stApp {{
                background: transparent !important;
                color: #ffffff !important;
            }}
            
            /* 2. Видео во весь экран */
            .video-bg {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                object-fit: cover;
                z-index: -2;
                pointer-events: none;
            }}

            /* 3. Оптимальное затемнение видео для читаемости (60% затемнения) */
            .video-overlay {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                background: rgba(0, 5, 15, 0.65);
                z-index: -1;
                pointer-events: none;
            }}

            /* 4. Стильные полупрозрачные карточки с БЕЛЫМ контрастным текстом */
            .custom-metric-box {{
                background: rgba(15, 23, 42, 0.65) !important;
                border: 1px solid rgba(255, 255, 255, 0.2) !important;
                border-radius: 15px !important;
                padding: 20px !important;
                color: #ffffff !important;
                backdrop-filter: blur(8px);
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            }}

            /* 5. Заголовки и тексты внутри карточек */
            .widget-title {{
                color: #38bdf8 !important; /* Яркий голубой цвет для заголовков */
                font-size: 1.3em !important;
                font-weight: 800 !important;
                margin-bottom: 12px !important;
            }}

            /* 6. Делаем весь общий текст приложения светлым */
            p, span, label, div {{
                color: #f1f5f9;
            }}
            
            /* 7. Подсветка названий накшатр */
            span[style*="color:#00d4ff"] {{
                color: #38bdf8 !important;
                text-shadow: 0 0 10px rgba(56, 189, 248, 0.5);
            }}

            /* Стилизация кнопки ИИ для максимальной читаемости */
            .stButton > button {{
                width: 100% !important;
                background: linear-gradient(135deg, rgba(30, 41, 59, 0.8), rgba(15, 23, 42, 0.9)) !important;
                color: #38bdf8 !important;
                border: 1px solid rgba(56, 189, 248, 0.4) !important;
                border-radius: 10px !important;
                padding: 12px 20px !important;
                font-weight: 600 !important;
                backdrop-filter: blur(8px) !important;
                transition: all 0.3s ease-in-out !important;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3) !important;
            }}

            .stButton > button:hover {{
                background: linear-gradient(135deg, rgba(56, 189, 248, 0.25), rgba(30, 41, 59, 0.9)) !important;
                color: #ffffff !important;
                border-color: #38bdf8 !important;
                box-shadow: 0 0 20px rgba(56, 189, 248, 0.6) !important;
                transform: translateY(-2px);
            }}
        </style>

        <video autoplay loop muted playsinline class="video-bg">
            <source src="data:video/mp4;base64,{b64_video}" type="video/mp4">
        </video>
        <div class="video-overlay"></div>
        """
        st.markdown(video_html, unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Ошибка видео-фона: {e}")

# Вызываем функцию
add_video_background()

@st.cache_resource
def init_engine():
    ts = load.timescale()
    eph = load('de421.bsp')
    return ts, eph

ts, eph = init_engine()

# --- СЛОВАРИ ---
ZODIAC_SIGNS = ["Овен", "Телец", "Близнецы", "Рак", "Лев", "Дева", "Весы", "Скорпион", "Стрелец", "Козерог", "Водолей", "Рыбы"]
NAKSHATRAS = [
    "Ашвини", "Бхарани", "Криттика", "Рохини", "Мригашира", "Ардра", 
    "Пунарвасу", "Пушья", "Ашлеша", "Магха", "Пурва-Пхалгуни", "Уттара-Пхалгуни", 
    "Хаста", "Читра", "Свати", "Вишакха", "Анурадха", "Джьешта", 
    "Мула", "Пурва-Ашадха", "Уттара-Ашадха", "Шравана", "Дханишта", 
    "Шатабхиша", "Пурва-Бхадрапада", "Уттара-Бхадрапада", "Ревати"
]
NAK_LORDS = ["Кету", "Венера", "Солнце", "Луна", "Марс", "Раху", "Юпитер", "Сатурн", "Меркурий"] * 3
NAK_TEXT_SYMBOLS = ["Голова лошади / Колесница / Целительство / Энергия", "Йони / Орган рождения / Очищение / Удача", "Лезвие / Пламя / Острие бритвы / Дух", "Повозка / Колесница / Храм / Росток / Жизнь", "Голова оленя / Сосуд с сомой / Поиск / Нектар", "Слеза / Алмаз / Буря / Влага / Хаос", "Лук / Стрелы / Саженец / Возврат / Обновление", "Вымя коровы / Цветок / Круг / Молоко / Питание", "Змея / Объятия / Узел / Скрытое / Интуиция", "Трон / Королевская палата / Предки / Власть", "Ножки кровати / Гамак / Слияние / Отдых", "Задние ножки / Кровать / Солнце / Процветание", "Ладонь / Кулак / Мастерство / Творчество / Сила", "Жемчужина / Сияющий камень / Зеркало / Красота", "Побег растения / Коралл / Ветер / Меч / Баланс", "Арка / Триумфальные ворота / Праздник / Успех", "Посох / Лотос / Круг / Порядок / Защита", "Амулет / Зонтик / Серьга / Защита / Лидер", "Связка корней / Лев / Слон / Глубина / Истина", "Веер / Сито / Корзина / Очищение / Выбор", "Бивень слона / Ножки кровати / Знание / Цель", "Ухо / Три следа / Стрела / Обучение / Слух", "Барабан / Музыка / Небо / Гром / Слава", "Пустой круг / 100 лекарей / Звезды / Магия", "Двуликий человек / Меч / Смерть / Переход", "Близнецы / Змея / Радуга / Поток / Глубина", "Рыба / Барабан / Море / Завершение / Вечность"]
PADA_LORDS_MAP = ["Марс", "Венера", "Меркурий", "Луна", "Солнце", "Меркурий", "Венера", "Марс", "Юпитер", "Сатурн", "Сатурн", "Юпитер"]
P_ICONS = {'Sun': '☀️ Sun', 'Moon': '🌙 Moon', 'Mars': '🔴 Mars', 'Mercury': '☿️ Merc', 'Jupiter': '🔵 Jup', 'Venus': '♀️ Venus', 'Saturn': '🪐 Sat', 'Rahu': '🐉 Rahu'}
Z_ICONS = {"Овен": "♈ Овен", "Телец": "♉ Телец", "Близнецы": "♊ Близн", "Рак": "♋ Рак", "Лев": "♌ Лев", "Дева": "♍ Дева", "Весы": "♎ Весы", "Скорпион": "♏ Скорп", "Стрелец": "♐ Стрел", "Козерог": "♑ Козер", "Водолей": "♒ Водол", "Рыбы": "♓ Рыбы"}

st.markdown("""
<style>
    .main-title { font-family: 'Lexend', sans-serif; font-weight: 800; font-size: 3em; color: white; margin: 0; }
    .sub-title { color: #94a3b8; font-size: 1.3em; letter-spacing: 5px; text-transform: uppercase; font-weight: 600; margin-top: -5px; }
    .moon-altar { background: linear-gradient(135deg, rgba(13,27,42,0.8) 0%, rgba(27,38,59,0.8) 100%); border-radius: 20px; padding: 30px; border: 1px solid #415a77; color: #e0e1dd; }
    .widget-title { color:#778da9; font-size: 1.6em; font-weight: 800; margin-bottom: 15px; text-transform: uppercase; }
    .custom-metric-box { background: rgba(65, 90, 119, 0.25); padding: 25px; border-radius: 15px; border: 1px solid #778da9; height: 100%; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# ⛔ БЛОК 2: ЯДРО РАСЧЕТОВ
# ============================================================
def get_dynamic_ayanamsa(t):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    return swe.get_ayanamsa(t.tt)

def deg_to_dms(decimal_deg):
    d = int(decimal_deg)
    m = int(round((decimal_deg - d) * 60))
    if m == 60:
        d += 1
        m = 0
    return f"{d}° {m:02d}'"

def format_cell(row):
    lon = row.get('Lon', 0)
    s_idx = int(lon/30); n_deg = 360/27; n_idx = int(lon / n_deg) % 27
    p_deg = n_deg / 4; pada = int((lon % n_deg) / p_deg) + 1; nav_idx = int((lon * 9) / 30) % 12
    
    deg_str = deg_to_dms(row['Deg'])
    
    # Добавляем инфо по Раху, если это он
    extra_str = ""
    if row.get('Planet') == 'Rahu':
        inv_deg = 30.0 - row['Deg']
        inv_d = int(inv_deg)
        inv_m = int((inv_deg - inv_d) * 60)
        extra_str = f" <span style='color:#fca5a5; font-size:0.9em;'>(обр: {inv_d}°{inv_m:02d}')</span>"

    return f"""<div style='font-size:1.25em; line-height:1.4;'><b>{P_ICONS.get(row['Planet'], row['Planet'])}</b> | {Z_ICONS[ZODIAC_SIGNS[s_idx]]} {deg_str}{extra_str}<br><span style='color:#00d4ff; font-weight:800; font-size:1.05em;'>{NAKSHATRAS[n_idx]}</span> ({NAK_LORDS[n_idx]})<br><span style='font-size:0.85em; color:#64748b;'>{NAK_TEXT_SYMBOLS[n_idx]}</span><br><span style='color:#475569; font-size:0.85em; font-weight:600;'>Пада {pada} | Упр: {PADA_LORDS_MAP[nav_idx]}</span></div>"""

def get_planet_data(t):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    flags = swe.FLG_SIDEREAL | swe.FLG_SWIEPH
    
    p_map = {
        'Sun': swe.SUN, 
        'Moon': swe.MOON, 
        'Mars': swe.MARS, 
        'Mercury': swe.MERCURY, 
        'Jupiter': swe.JUPITER, 
        'Venus': swe.VENUS, 
        'Saturn': swe.SATURN
    }
    
    res = []
    for name, obj_id in p_map.items():
        pos, _ = swe.calc_ut(t.ut1, obj_id, flags)
        lon = pos[0]
        res.append({'Planet': name, 'Lon': lon, 'Deg': lon % 30})
        
    df = pd.DataFrame(res).sort_values(by='Deg', ascending=False).reset_index(drop=True)
    roles = ['AK', 'AmK', 'BK', 'MK', 'PiK', 'GK', 'DK']
    df['Role'] = (roles + ['-']*5)[:len(df)]
    
    # Точный расчет Истинного Раху (True Node)
    pos_rahu, _ = swe.calc_ut(t.ut1, swe.TRUE_NODE, flags)
    ra_lon = pos_rahu[0]
    ra_row = pd.DataFrame([{'Planet': 'Rahu', 'Lon': ra_lon, 'Deg': ra_lon % 30, 'Role': '-'}])
    
    return pd.concat([df, ra_row], ignore_index=True)

def get_lunar_full_data(t_now):
    earth = eph['earth']
    def get_diff(t_v):
        s = earth.at(t_v).observe(eph['sun']).ecliptic_latlon()[1].degrees
        m = earth.at(t_v).observe(eph['moon']).ecliptic_latlon()[1].degrees
        return (m - s) % 360
    def find_nearest(target):
        curr = t_now.utc_datetime()
        for d in range(32):
            check_t = ts.utc(curr + timedelta(days=d))
            diff = (get_diff(check_t) - target + 180) % 360 - 180
            if abs(diff) < 15:
                sub_curr = check_t.utc_datetime() - timedelta(days=1)
                for m in range(2880):
                    precise_t = ts.utc(sub_curr + timedelta(minutes=m))
                    if abs((get_diff(precise_t) - target + 180) % 360 - 180) < 0.1: return precise_t.utc_datetime()
        return curr
    f_dt = find_nearest(180); n_dt = find_nearest(0); now_diff = get_diff(t_now); ayan = get_dynamic_ayanamsa(t_now)
    m_lon = (earth.at(t_now).observe(eph['moon']).ecliptic_latlon()[1].degrees - ayan) % 360
    return {"tithi": math.ceil(now_diff / 12) or 1, "phase_icon": ["🌑","🌒","🌓","🌔","🌕","🌖","🌗","🌘"][int(((now_diff + 22.5) % 360) / 45)], "illum": (1 - math.cos(math.radians(now_diff))) / 2 * 100, "sign": ZODIAC_SIGNS[int(m_lon/30)], "nak": NAKSHATRAS[int(m_lon/(360/27))%27], "full_dt": f_dt + timedelta(hours=3), "new_dt": n_dt + timedelta(hours=3)}

def find_rotations(start_dt):
    events = []
    t_start = ts.utc(start_dt.year, start_dt.month, start_dt.day, start_dt.hour, start_dt.minute)
    df_now = get_planet_data(t_start); current_pair = f"{df_now.iloc[0]['Planet']}-{df_now.iloc[1]['Planet']}"
    
    for i in range(1, 20160, 3):
        t_check_dt = start_dt - timedelta(minutes=i)
        df_p = get_planet_data(ts.utc(t_check_dt.year, t_check_dt.month, t_check_dt.day, t_check_dt.hour, t_check_dt.minute))
        if f"{df_p.iloc[0]['Planet']}-{df_p.iloc[1]['Planet']}" != current_pair:
            events.append({"type": "Прошлая", "dt": t_check_dt + timedelta(hours=3), "ak": df_p.iloc[0], "amk": df_p.iloc[1]}); break
            
    for i in range(1, 20160, 3):
        t_check_dt = start_dt + timedelta(minutes=i)
        df_f = get_planet_data(ts.utc(t_check_dt.year, t_check_dt.month, t_check_dt.day, t_check_dt.hour, t_check_dt.minute))
        if f"{df_f.iloc[0]['Planet']}-{df_f.iloc[1]['Planet']}" != current_pair:
            events.append({"type": "Следующая", "dt": t_check_dt + timedelta(hours=3), "ak": df_f.iloc[0], "amk": df_f.iloc[1]}); break
            
    return events

# ============================================================
# ⛔ БЛОК 3: ИНТЕРФЕЙС
# ============================================================
st.markdown(f"""<div class="header-box"><h1 class="main-title">JULIA ASSISTANT</h1><div class="sub-title">Astro coordination center</div></div>""", unsafe_allow_html=True)

# --- АНИМИРОВАННЫЙ БАННЕР ---
img_data = get_image_base64("Gemini_Generated_Image_vtbwtcvtbwtcvtbw.png")

if img_data:
    part1 = "<style>.space-banner-new { width: 100%; height: 300px; border-radius: 15px; background-image: url('data:image/jpeg;base64,"
    part2 = img_data
    part3 = "'); background-size: 100%; background-position: center; background-repeat: no-repeat; box-shadow: 0 10px 20px rgba(0,0,0,0.6); margin-bottom: 25px; animation: spaceDrift 20s ease-in-out infinite alternate; } @keyframes spaceDrift { 0% { background-size: 100%; background-position: center; } 100% { background-size: 115%; background-position: center 60%; } }</style><div class='space-banner-new'></div>"
    
    banner_html = part1 + part2 + part3
    st.markdown(banner_html, unsafe_allow_html=True)

t1, t2 = st.tabs(["📊 ПРЯМОЙ ЭФИР", "📅 ПЛАНИРОВЩИК"])

with t1:
    now_u = datetime.utcnow(); t_n = ts.utc(now_u.year, now_u.month, now_u.day, now_u.hour, now_u.minute)
    df_n = get_planet_data(t_n); l = get_lunar_full_data(t_n)
    
    st.subheader("🌙 Лунный Алтарь")
    st.markdown(f"""<div class="moon-altar"><div style="display: flex; justify-content: space-between; align-items: center;"><div><div style="font-size: 5em; line-height:1;">{l['phase_icon']}</div><div style="font-size: 2.5em; font-weight: bold;">{l['tithi']} лунные сутки</div></div><div style="text-align: right;"><div style="font-size: 2.2em; font-weight: bold;">{l['sign']}</div><div style="color: #00d4ff; font-size:1.6em; font-weight:bold;">{l['nak']}</div></div></div><div style="margin: 25px 0 5px 0;"><small style="color:#778da9; text-transform: uppercase; font-size:1.1em;">Освещенность: {int(l['illum'])}%</small><div style="background: rgba(255,255,255,0.1); height: 18px; border-radius: 9px; margin-top:10px;"><div style="background: linear-gradient(to right, #00d4ff, #e0e1dd); width: {l['illum']}%; height: 18px; border-radius: 9px; box-shadow: 0 0 20px #00d4ff;"></div></div></div><div style="display: flex; justify-content: space-between; font-size: 1.25em; margin-top: 30px; border-top: 1px solid rgba(255,255,255,0.1); padding-top:20px;"><div>🌕 <b>Полнолуние:</b><br>{l['full_dt'].strftime('%d.%m %H:%M')}</div><div style="text-align: right;">🌑 <b>Новолуние:</b><br>{l['new_dt'].strftime('%d.%m %H:%M')}</div></div></div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    
    # ==========================================
    # Модуль ИИ (gemini-2.5-flash с учетом Раху и Карака)
    # ==========================================
    GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", "")
    
    if st.button("🤖 Сгенерировать ИИ-прогноз по Луне и Каракам (Forex & XAUUSD)", use_container_width=True):
        if not GOOGLE_API_KEY:
            st.error("⚠️ Ошибка: На сервере не настроен GOOGLE_API_KEY в разделе Secrets!")
        else:
            with st.spinner("Анализирую нейро-астрологические связи (AK, AmK, Раху)..."):
                try:
                    genai.configure(api_key=GOOGLE_API_KEY)
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    
                    ak_p = df_n.iloc[0]['Planet']
                    amk_p = df_n.iloc[1]['Planet']
                    sun_row = df_n[df_n['Planet'] == 'Sun'].iloc[0]
                    sun_sign = ZODIAC_SIGNS[int(sun_row['Lon'] / 30)]
                    
                    prompt = f"""
Ты — профессиональный финансовый астролог и квантовый аналитик рынков.
Проведи экспресс-анализ текущего астрологического контекста:
1. ЛУНА: Знак {l['sign']}, Накшатра {l['nak']}, Освещенность {int(l['illum'])}%.
2. СОЛНЦЕ (Индикатор ЗОЛОТА XAUUSD): Знак {sun_sign}.
3. ATMAKARAKA (AK): {ak_p}.
4. AMATYAKARAKA (AmK): {amk_p}.
5. РАХУ: Активен в транзитах (фактор спекуляций, ложных пробоев и резких импульсов).

Сформируй лаконичный отчёт (до 200 слов) по структуре:
• 🧠 Психологический фон рынка (Луна + AK {ak_p}).
• 👥 Поведение толпы и трейдеров (AmK {amk_p}).
• ⚡ Forex & Волатильность (учет фактора Раху).
• 🏆 Золото (XAUUSD): фокус через Солнце в {sun_sign}.
"""
                    response = model.generate_content(prompt)
                    st.info(response.text)
                except Exception as e:
                    st.error(f"Сбой связи с ИИ-оракулом: {e}")
    
    st.markdown("<br>", unsafe_allow_html=True)

    st.subheader("👑 Основные Караки")
    c1, c2 = st.columns(2)
    with c1: st.markdown(f'<div class="custom-metric-box"><div class="widget-title">💎 ATMAKARAKA</div>{format_cell(df_n.iloc[0])}</div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="custom-metric-box"><div class="widget-title">🥈 AMATYAKARAKA</div>{format_cell(df_n.iloc[1])}</div>', unsafe_allow_html=True)

    st.subheader("🔄 Ближайшие смены ротаций")
    rots = find_rotations(now_u); rc1, rc2 = st.columns(2)
    for r in rots:
        with (rc1 if r['type']=="Прошлая" else rc2):
            st.markdown(f"""<div class="custom-metric-box" style="background:rgba(255,255,255,0.03)"><div class="widget-title">{r['type'].upper()} ({r['dt'].strftime('%H:%M')})</div><div style="color:#00d4ff; font-weight:bold; margin-bottom:10px;">{r['dt'].strftime('%d.%m.%Y')}</div><div style="display:grid; grid-template-columns: 1fr 1fr; gap:15px;"><div><small style="color:#778da9">АК</small><br>{format_cell(r['ak'])}</div><div><small style="color:#778da9">AmK</small><br>{format_cell(r['amk'])}</div></div></div>""", unsafe_allow_html=True)

    st.subheader("📋 Таблица карак")
    df_v = df_n.copy(); df_v['Детализация'] = df_v.apply(format_cell, axis=1)
    st.write(df_v[['Role', 'Planet', 'Deg', 'Детализация']].to_html(escape=False, index=False).replace('\n', ''), unsafe_allow_html=True)

    st.subheader("🐉 Раху (True Node)")
    ra_val = df_n[df_n['Planet'] == 'Rahu'].iloc[0]
    wr1, wr2 = st.columns([1, 2])
    with wr1: st.markdown(f'<div class="custom-metric-box" style="border-color:#ff4b4b;"><div class="widget-title">ТЕКУЩИЙ РАХУ</div>{format_cell(ra_val)}</div>', unsafe_allow_html=True)
    with wr2: st.markdown("""<div style="font-size:1.2em; padding:25px; background:rgba(255,75,75,0.05); border-radius:15px; border:1px solid #ff4b4b; line-height:1.6;"><b>Ингрессии Раху:</b><br>• Рыбы: до 18.05.2025<br>• <b style='color:#00d4ff;'>Водолей: с 18.05.2025 по 05.12.2026</b><br>• Козерог: с 05.12.2026</div>""", unsafe_allow_html=True)

with t2:
    st.subheader("⚙️ Сетка планирования")
    cx, cy = st.columns(2)
    with cx: ds = st.date_input("Начало", datetime.now()); ts_i = st.time_input("Старт", time(0, 0))
    with cy: de = st.date_input("Конец", datetime.now() + timedelta(days=2)); te_i = st.time_input("Финиш", time(23, 59))
    
    st.markdown("""
    <style>
        div[data-testid="stAppViewBlockContainer"] { opacity: 1 !important; filter: none !important; }
        [data-testid="stApp"]::before { display: none !important; }
    </style>
    """, unsafe_allow_html=True)
    
    if st.button("🚀 ПОСТРОИТЬ ТАБЛИЦУ РОТАЦИЙ"):
        status_text = st.empty()
        p_bar = st.empty()
        
        status_text.markdown("⏳ **Идет синхронизация с эфемеридами и расчет. Пожалуйста, подождите...**")
        progress_bar = p_bar.progress(0)
        
        s_u = datetime.combine(ds, ts_i) - timedelta(hours=3)
        e_u = datetime.combine(de, te_i) - timedelta(hours=3)
        results = []; curr = s_u; last_p = ""
        
        total_sec = (e_u - s_u).total_seconds()
        step_min = 3 
        total_steps = max(int(total_sec / (step_min * 60)), 1)
        current_step = 0
        
        days_ru = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]
        
        while curr < e_u:
            t_ev = ts.utc(curr.year, curr.month, curr.day, curr.hour, curr.minute)
            df_ev = get_planet_data(t_ev)
            
            new_p = f"{df_ev.iloc[0]['Planet']}-{df_ev.iloc[1]['Planet']}"
            if new_p != last_p:
                sun = df_ev[df_ev['Planet']=='Sun'].iloc[0]
                moon = df_ev[df_ev['Planet']=='Moon'].iloc[0]
                local_dt = curr + timedelta(hours=3)
                
                results.append({
                    "Дата": local_dt.strftime("%d.%m.%Y"),
                    "День недели": days_ru[local_dt.weekday()],
                    "Время": local_dt.strftime("%H:%M"),
                    "💎 АК": format_cell(df_ev.iloc[0]),
                    "🥈 AmK": format_cell(df_ev.iloc[1]),
                    "☀️ Солнце": format_cell(sun),
                    "🌙 Луна": format_cell(moon)
                })
                last_p = new_p
            
            curr += timedelta(minutes=step_min)
            current_step += 1
            
            if current_step % 10 == 0 or current_step == total_steps:
                progress_bar.progress(min(current_step / total_steps, 1.0))
        
        status_text.empty()
        p_bar.empty()

        if results:
            df_res = pd.DataFrame(results)
            raw_html = df_res.to_html(escape=False, index=False).replace('\n', '')
            print_title = f"График ротаций с {ds.strftime('%d.%m.%Y')} по {de.strftime('%d.%m.%Y')}"
            
            html_btn = f"""
            <script>
            function openPrint() {{
                const win = window.open('', '_blank');
                win.document.write(`<html><head><title>Печать</title>
                <style>
                    @page {{ size: landscape; margin: 10mm; }} 
                    body {{ font-family: sans-serif; padding: 20px; }}
                    h2 {{ text-align: center; color: #333; margin-bottom: 20px; }}
                    table {{ border-collapse: collapse; width: 100%; }} 
                    th, td {{ border: 1px solid #000; padding: 6px; font-size: 10px; text-align: left; }}
                    th {{ background-color: #f2f2f2; }}
                </style>
                </head><body>
                    <h2>{print_title}</h2>
                    {raw_html}
                </body></html>`);
                win.document.close();
                setTimeout(() => {{ win.print(); }}, 500);
            }}
            </script>
            <button onclick="openPrint()" style="width:100%; padding:15px; background:#28a745; color:white; border:none; border-radius:8px; cursor:pointer; font-weight:bold; font-size:16px; font-family:sans-serif; box-shadow: 0 4px 6px rgba(0,0,0,0.1); margin-bottom: 10px;">🖨️ ПЕЧАТЬ ТАБЛИЦЫ (АЛЬБОМНЫЙ ФОРМАТ)</button>
            """
            components.html(html_btn, height=75)
            st.write(df_res.to_html(escape=False, index=False), unsafe_allow_html=True)