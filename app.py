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

# Инициализируем данные баннера в самом начале
img_data = get_image_base64("Gemini_Generated_Image_vtbwtcvtbwtcvtbw.png")

# ============================================================
# ⛔ БЛОК 1: КОНФИГУРАЦИЯ И СТИЛИ
# ============================================================
st.set_page_config(page_title="Julia Assistant", layout="wide")

def add_video_background(video_path="space_background.mp4"):
    try:
        with open(video_path, "rb") as f:
            video_bytes = f.read()
        b64_video = base64.b64encode(video_bytes).decode()
        
        video_html = f"""
        <style>
            .stApp {{
                background: transparent !important;
                color: #ffffff !important;
            }}
            
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

            .custom-metric-box {{
                background: rgba(15, 23, 42, 0.65) !important;
                border: 1px solid rgba(255, 255, 255, 0.2) !important;
                border-radius: 15px !important;
                padding: 20px !important;
                color: #ffffff !important;
                backdrop-filter: blur(8px);
                box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
            }}

            .widget-title {{
                color: #38bdf8 !important;
                font-size: 1.3em !important;
                font-weight: 800 !important;
                margin-bottom: 12px !important;
            }}

            p, span, label, div {{ color: #f1f5f9; }}
            
            span[style*="color:#00d4ff"] {{
                color: #38bdf8 !important;
                text-shadow: 0 0 10px rgba(56, 189, 248, 0.5);
            }}

            /* СТИЛИЗАЦИЯ КНОПКИ ИИ (БЕЗ БЕЛОЙ ПОЛОСЫ) */
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

            div[data-testid="stTable"], div[data-testid="stDataFrame"] {{
                background: rgba(15, 23, 42, 0.75) !important;
                border-radius: 12px !important;
                border: 1px solid rgba(255, 255, 255, 0.15) !important;
                backdrop-filter: blur(8px);
                padding: 10px !important;
            }}

            .gandanta-badge {{
                display: inline-block;
                background: rgba(239, 68, 68, 0.25);
                color: #fca5a5 !important;
                border: 1px solid #ef4444;
                padding: 2px 8px;
                border-radius: 6px;
                font-size: 0.8em;
                font-weight: bold;
                letter-spacing: 0.5px;
                box-shadow: 0 0 10px rgba(239, 68, 68, 0.5);
                animation: pulse-gandanta 2s infinite;
            }}

            @keyframes pulse-gandanta {{
                0% {{ box-shadow: 0 0 5px rgba(239, 68, 68, 0.4); }}
                50% {{ box-shadow: 0 0 15px rgba(239, 68, 68, 0.9); }}
                100% {{ box-shadow: 0 0 5px rgba(239, 68, 68, 0.4); }}
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

# --- АСТРОЛОГИЧЕСКИЕ ФУНКЦИИ ---
def check_gandanta(lon_deg):
    gandanta_zones = [
        (359.0, 360.0), (0.0, 1.0),
        (119.0, 120.0), (120.0, 121.0),
        (239.0, 240.0), (240.0, 241.0)
    ]
    for start, end in gandanta_zones:
        if start <= lon_deg <= end:
            return True
    return False

def get_julian_day(dt):
    return swe.julday(dt.year, dt.month, dt.day, dt.hour + dt.minute/60.0 + dt.second/3600.0)

def get_lahiri_sidereal(jd, planet_id):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    res, _ = swe.calc_ut(jd, planet_id, swe.FLG_SIDEREAL)
    return res[0] % 360

def get_rahu_true(jd):
    swe.set_sid_mode(swe.SIDM_LAHIRI)
    res, _ = swe.calc_ut(jd, swe.MEAN_NODE, swe.FLG_SIDEREAL)
    return res[0] % 360

def get_nakshatra_info(lon):
    nak_num = int(lon / (360 / 27))
    pada = int((lon % (360 / 27)) / (360 / 108)) + 1
    rem_deg = lon % (360 / 27)
    deg_in_nak = int(rem_deg)
    min_in_nak = int((rem_deg - deg_in_nak) * 60)
    total_sign_num = int(lon / 30)
    p_lord = PADA_LORDS_MAP[(total_sign_num * 3 + (pada - 1)) % 12]
    return {
        'num': nak_num + 1, 'name': NAKSHATRAS[nak_num], 'lord': NAK_LORDS[nak_num],
        'pada': pada, 'pada_lord': p_lord, 'deg': deg_in_nak, 'min': min_in_nak,
        'symbol': NAK_TEXT_SYMBOLS[nak_num]
    }

def get_moon_metrics(dt):
    jd = get_julian_day(dt)
    m_lon = get_lahiri_sidereal(jd, swe.MOON)
    s_lon = get_lahiri_sidereal(jd, swe.SUN)
    
    m_sign = ZODIAC_SIGNS[int(m_lon / 30)]
    nak_info = get_nakshatra_info(m_lon)
    
    angle = (m_lon - s_lon) % 360
    illum = (1 - math.cos(math.radians(angle))) / 2 * 100
    
    return {
        'sign': m_sign, 'nak': nak_info['name'], 'pada': nak_info['pada'],
        'nak_lord': nak_info['lord'], 'pada_lord': nak_info['pada_lord'],
        'symbol': nak_info['symbol'], 'illum': illum, 'lon': m_lon
    }

def calculate_karakas(dt):
    jd = get_julian_day(dt)
    planets = {
        'Sun': swe.SUN, 'Moon': swe.MOON, 'Mars': swe.MARS,
        'Mercury': swe.MERCURY, 'Jupiter': swe.JUPITER,
        'Venus': swe.VENUS, 'Saturn': swe.SATURN
    }
    
    p_data = []
    for name, p_id in planets.items():
        lon = get_lahiri_sidereal(jd, p_id)
        deg_in_sign = lon % 30
        p_data.append({'Planet': name, 'Lon': lon, 'DegInSign': deg_in_sign, 'CharDeg': deg_in_sign})
        
    r_lon = get_rahu_true(jd)
    r_deg_in_sign = r_lon % 30
    p_data.append({'Planet': 'Rahu', 'Lon': r_lon, 'DegInSign': r_deg_in_sign, 'CharDeg': 30.0 - r_deg_in_sign})
    
    df = pd.DataFrame(p_data)
    df = df.sort_values(by='CharDeg', ascending=False).reset_index(drop=True)
    
    karaka_names = ['AK', 'AmK', 'BK', 'MK', 'PK', 'GK', 'DK', '8K']
    df['Karaka'] = karaka_names[:len(df)]
    return df

GOOGLE_API_KEY = st.secrets.get("GOOGLE_API_KEY", "")

# ============================================================
# ⛔ БЛОК 2: ПРЯМОЙ ЭФИР И ИИ-ПРОГНОЗ
# ============================================================

# ВЕРХНИЙ ПРОЗРАЧНЫЙ БЛОК-«ВОЗДУХ» ДЛЯ ОБЗОРА ЧЕРНОЙ ДЫРЫ В ФОНЕ
st.markdown("<div style='height: 180px;'></div>", unsafe_allow_html=True)

now_utc = datetime.utcnow()
l = get_moon_metrics(now_utc)
df_n = calculate_karakas(now_utc)

header_box = f"""
<div class="custom-metric-box" style="margin-bottom: 25px;">
    <div style="font-size: 1.1em; font-weight: 600; color: #94a3b8; margin-bottom: 8px;">
        📡 ПРЯМОЙ ЭФИР (UTC): <span style="color: #ffffff;">{now_utc.strftime('%Y-%m-%d %H:%M:%S')}</span>
    </div>
    <div style="font-size: 1.25em; line-height: 1.6;">
        🌙 <b>Луна в знаке:</b> <span style="color:#00d4ff">{l['sign']}</span> | 
        <b>Накшатра:</b> <span style="color:#00d4ff">{l['nak']}</span> (Пада {l['pada']}) | 
        <b>Освещенность:</b> <span style="color:#00d4ff">{int(l['illum'])}%</span><br>
        👑 <b>Управитель Накшатры:</b> <span style="color:#00d4ff">{l['nak_lord']}</span> | 
        <b>Управитель Пады:</b> <span style="color:#00d4ff">{l['pada_lord']}</span><br>
        🎨 <b>Символ / Грахи:</b> <span style="color:#e2e8f0">{l['symbol']}</span>
    </div>
</div>
"""
st.markdown(header_box, unsafe_allow_html=True)

# ИИ-кнопка и генератор
if st.button("🤖 Сгенерировать ИИ-прогноз по Луне и Каракам (Forex & XAUUSD)", use_container_width=True):
    if not GOOGLE_API_KEY:
        st.error("⚠️ Ошибка: В секретах не настроен GOOGLE_API_KEY!")
    else:
        with st.spinner("Анализирую нейро-астрологические связи (AK, AmK, Раху, Солнце, Луна)..."):
            try:
                genai.configure(api_key=GOOGLE_API_KEY)
                model = genai.GenerativeModel('gemini-2.5-flash')
                
                ak_planet = df_n.iloc[0]['Planet']
                amk_planet = df_n.iloc[1]['Planet']
                bk_planet = df_n.iloc[2]['Planet']
                
                sun_row = df_n[df_n['Planet'] == 'Sun'].iloc[0]
                sun_sign = ZODIAC_SIGNS[int(sun_row['Lon'] / 30)]
                
                rahu_context = ""
                if ak_planet == 'Rahu' or amk_planet == 'Rahu':
                    rahu_context = f"ОСОБЫЙ АКЦЕНТ: Раху задействован в главных караках! Третья планета контекста (BK): {bk_planet}. Учти Раху как фактор непредсказуемости, спекулятивных выбросов, ложных пробоев и аномалий на рынке."
                
                prompt = f"""
Ты — ведущий мировой финансовый астролог и квантовый аналитик товарно-сырьевых и валютных рынков.
Проведи комплексный экспресс-анализ текущего астрологического контекста:

1. ЛУНА (Быстрый ПНР — психологический настрой рынка): Знак {l['sign']}, Накшатра {l['nak']}, Освещенность {int(l['illum'])}%.
2. СОЛНЦЕ (Главный управитель и индикатор ЗОЛОТА XAUUSD): Знак {sun_sign}.
3. ATMAKARAKA (AK — Базовый психологический вектор рынка): {ak_planet}.
4. AMATYAKARAKA (AmK — Инструмент и способ действий толпы/трейдеров): {amk_planet}.
{rahu_context}

Сформируй лаконичный аналитический отчёт (до 200 слов) по следующей структуре:
• 🧠 Психологический фон (ПНР): Опиши сочетание Луны и AK ({ak_planet}) — эмоции и глубинное состояние участников рынка.
• 👥 Поведение толпы (AmK): Как действуют массы под управлением {amk_planet} (импульсивность, страх, выжидание, агрессия).
• ⚡ Forex & Волатильность: Общий вектор движений и риски ложных импульсов.
• 🏆 Золото (XAUUSD): Детальный фокус на золото через призму Солнца в {sun_sign}, Луны и статус Раху.
"""
                response = model.generate_content(prompt)
                st.info(response.text)
            except Exception as e:
                st.error(f"Сбой связи с ИИ-оракулом: {e}")

# ============================================================
# ⛔ БЛОК 3: ИНТЕРАКТИВНЫЙ КАЛЬКУЛЯТОР ТАБЛИЦ
# ============================================================
st.markdown("<br>", unsafe_allow_html=True)
st.subheader("📅 Интерактивный калькулятор Чара Карак")

col1, col2 = st.columns(2)
with col1:
    d_input = st.date_input("Выберите дату", now_utc.date())
with col2:
    t_input = st.time_input("Выберите время (UTC)", now_utc.time())

dt_calc = datetime.combine(d_input, t_input)
df_res = calculate_karakas(dt_calc)

def build_display_table(df_input):
    display_data = []
    for idx, row in df_input.iterrows():
        p_name = row['Planet']
        p_icon = P_ICONS.get(p_name, p_name)
        sign_name = ZODIAC_SIGNS[int(row['Lon'] / 30)]
        z_icon = Z_ICONS.get(sign_name, sign_name)
        
        deg_val = int(row['DegInSign'])
        min_val = int((row['DegInSign'] - deg_val) * 60)

        if p_name == 'Rahu':
            inv_deg = row['CharDeg']
            inv_d = int(inv_deg)
            inv_m = int((inv_deg - inv_d) * 60)
            deg_str = f"{deg_val}°{min_val:02d}' ({inv_d}°{inv_m:02d}')"
        else:
            deg_str = f"{deg_val}°{min_val:02d}'"

        nak_info = get_nakshatra_info(row['Lon'])
        nak_str = f"{nak_info['name']} ({nak_info['pada']} пада)"

        is_g = check_gandanta(row['Lon'])
        if is_g:
            nak_str += " <span class='gandanta-badge'>⚠️ ГАНДАНТА</span>"

        display_data.append({
            'Карака': f"<b>{row['Karaka']}</b>",
            'Планета': p_icon,
            'Знак': z_icon,
            'Градус в знаке': deg_str,
            'Накшатра': nak_str
        })
    return pd.DataFrame(display_data)

df_table = build_display_table(df_res)
st.write(df_table.to_html(escape=False, index=False), unsafe_allow_html=True)

# ============================================================
# ⛔ БЛОК 4: НИЖНИЙ БАННЕР (ПОД ВСЕМИ ТАБЛИЦАМИ)
# ============================================================
st.markdown("<br><hr style='border-color: rgba(255,255,255,0.1);'><br>", unsafe_allow_html=True)

if img_data:
    part1 = "<style>.space-banner-new { width: 100%; height: 280px; border-radius: 15px; background-image: url('data:image/jpeg;base64,"
    part2 = img_data
    part3 = "'); background-size: cover; background-position: center; background-repeat: no-repeat; box-shadow: 0 10px 25px rgba(0,0,0,0.7); margin-top: 20px; margin-bottom: 30px; animation: spaceDrift 20s ease-in-out infinite alternate; } @keyframes spaceDrift { 0% { background-size: 100%; background-position: center; } 100% { background-size: 110%; background-position: center 60%; } }</style><div class='space-banner-new'></div>"
    
    banner_html = part1 + part2 + part3
    st.markdown(banner_html, unsafe_allow_html=True)